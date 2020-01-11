'''
    部分数据接口对接
'''
from src.utils.sessions import FuturesSession
from src.service.HtmlService import get_response, get_absolute_url_path, get_parsed_href_html, extract_jsonp
from src.utils import date
import datetime
import json
from src.utils.date import get_english_month, get_ambiguous_date, full_time_format, parse_date_str, date_obj_to_timestamp
from bs4 import BeautifulSoup
from src.service.StockService import StockService

session = FuturesSession(max_workers=1)

client = StockService.getMongoInstance()
financial_calendar_document = client.stock.financial_calendar
base_document = client.stock.base

class DataService(object):

    # 获取农产品指数(deprecated)
    @staticmethod
    def get_farm_product_index(code):
        # 页面地址（全国农产品商务信息公共服务平台-价格指数）：http://nc.mofcom.gov.cn/zhuanti/ap88/jgzs.shtml（已失效）
        url = "http://www.chinaap.com/chinaapindex/index/getBrokenLine"
        params = {
            "goodsId": code
        }
        content = session.post(url, data=params).result().content
        result = json.loads(content)
        return result

    # 获取shibor数据，按照官方约定，最多能获取一年
    @staticmethod
    def get_shibor_data(start=None, end=None):
        url = 'http://www.chinamoney.com.cn/ags/ms/cm-u-bk-shibor/ShiborHis'
        if start is None:
            raise Exception('请选择开始日期')
        if end is None:
            raise Exception('请选择结束日期')
        params = {
            "lang": "cn",
            "startDate": start,
            "endDate": end,
            "t": date.getCurrentTimestamp()
        }

        return json.loads(session.get(url, params=params).result().content.decode())

    # 拉取国家统计局指定数据
    @staticmethod
    def get_stat_info(code = 'A020F01'):
        url = 'http://data.stats.gov.cn/easyquery.htm'
        params = {
            'm': 'QueryData',
            'dbcode': 'hgyd',
            'rowcode': 'zb',
            'colcode': 'sj',
            'wds': '[]',
            'dfwds': '[{"wdcode": "zb", "valuecode": "' + code +'"}]'
        }

        response = json.loads(get_response(url, params=params))

        data = response['returndata']

        specification = data['wdnodes'][0]['nodes'][0]

        result = {
            "name": specification['cname'],
            "memo": specification['memo'],
            "unit": specification['unit'],
            'list': []
        }

        for item in data['datanodes']:
            # 数据强校验
            if item['wds'][0]['valuecode'] == code:
                date_str = item['code'].split('.')[-1]
                value = item['data']['data']
                result['list'].append({
                    "date": date_str,
                    "value": value
                })

        return result

    # 获取 CNN恐慌贪婪指数
    @staticmethod
    def get_cnn_fear_greed_index():
        def extract_value(text):
            return int(str.strip(text.split('(')[0].split(':')[-1]))

        url = 'https://money.cnn.com/data/fear-and-greed/'
        raw_html = get_response(url)
        html = BeautifulSoup(raw_html, 'html.parser')
        index_indicator = html.select_one("#needleChart ul")
        if index_indicator is None:
            raise Exception('cnn fear & greed index indicator is none')

        date_text = html.select_one('#needleAsOfDate').text.split(' at ')[0].split(' ')

        release_date = get_ambiguous_date(get_english_month(date_text[-2]), int(date_text[-1]))
        model = {
            "release_date": release_date,
            "id": release_date,
            "indicator_list": []
        }
        li_list = index_indicator.contents

        if 'Now' not in li_list[0].text:
            raise Exception('数据异常')
        model['now'] = extract_value(li_list[0].text)

        if 'Previous Close' not in li_list[1].text:
            raise Exception('数据异常')
        model['yesterday'] = extract_value(li_list[1].text)

        if '1 Week Ago' not in li_list[2].text:
            raise Exception('数据异常')
        model['oneWeekAgo'] = extract_value(li_list[2].text)

        if '1 Month Ago' not in li_list[3].text:
            raise Exception('数据异常')
        model['oneMonthAgo'] = extract_value(li_list[3].text)

        if '1 Year Ago' not in li_list[4].text:
            raise Exception('数据异常')
        model['oneYearAgo'] = extract_value(li_list[4].text)

        detail_indicator_container = html.select_one(".indicatorContainer")
        if detail_indicator_container is None:
            raise Exception('数据异常')

        for detail_indicator in detail_indicator_container.children:
            label = detail_indicator.select_one('.label .wsod_fLeft').text
            level = detail_indicator.select_one('.label .wsod_fRight').text
            description_list = detail_indicator.select('.detail .wsod_fLeft p')

            model['indicator_list'].append({
                "label": label,
                "level": level,
                "description": description_list[0].text,
                "lastChangedAt": description_list[1].text,
                "lastUpdateAt": description_list[2].text
            })

        return model

    # 获取美债收益率
    @staticmethod
    def get_american_securities_yield():
        url = 'https://sbcharts.investing.com/bond_charts/bonds_chart_1.json'
        response = get_response(url)
        data_json = json.loads(response)
        update_date = data_json['last_updated'][:10]

        current = data_json['current']
        current_data_map = {}
        for item in current:
            current_data_map[item[0]] = item[1]

        for item_date in ['1M', '3M', '6M', '1Y', '2Y', '3Y', '10Y']:
            if item_date not in current_data_map:
                raise Exception('数据错误')

        return {
            "release_date": update_date,
            "id": update_date,
            "data": current_data_map
        }

    # 获取央行公开市场操作最近数据
    @staticmethod
    def get_latest_central_bank_open_market_operation():
        url = 'http://www.chinamoney.com.cn/ags/ms/cm-s-notice-query/contents'
        params = {
            "pageNo": '1',
            "pageSize": "5",
            "channelId": '2845'
        }
        response = get_response(url, params=params)
        response_json = json.loads(response)
        records = response_json['records']

        result = []
        for record in records:
            if '公开市场' not in record['title']:
                continue

            content_url = get_absolute_url_path(url, record['draftPath'])
            content_raw_html = get_response(content_url)
            content_raw_html = get_parsed_href_html(url, content_raw_html)
            content_html = BeautifulSoup(content_raw_html, 'html.parser')
            content_body = content_html.select_one(".article-a-content > div")
            if content_body is None:
                raise Exception('数据异常')

            model = {
                "title": record['title'],
                "id": record['channelId'] + '_' + record['contentId'],
                "release_date": record['releaseDate'],
                "html": str(content_body)
            }

            result.append(model)

        return result

    # 获取 LPR 最新数据
    @staticmethod
    def get_latest_lpr_biding():
        url = 'http://www.chinamoney.com.cn/r/cms/www/chinamoney/data/currency/bk-lpr.json'
        response = get_response(url)
        response_json = json.loads(response)
        records = response_json['records']

        biding_map = {}
        for record in records:
            biding_map[record['termCode']] = float(record['shibor'])

        if '1Y' not in biding_map or '5Y' not in biding_map:
            raise Exception('数据异常')

        release_date = response_json['data']['showDateCN'][:10]
        return {
            "release_date": release_date,
            "id": release_date,
            "data": biding_map
        }

    @staticmethod
    def resolve_fx_live_item(item, date_time_str):
        important = item.select_one(".zb_word .red_color_f") is not None
        model = {
            'macro': False,  # 是否是宏观数据
            "isImportant": important,
            "imageList": [],
            "isTop": False,  # 是否置顶
            "timestamp": date_obj_to_timestamp(parse_date_str(date_time_str, format_rule=full_time_format))
        }

        title_item = item.select_one(".zb_word")
        if title_item is None:
            # 经济数据
            title_element = item.select_one('.zb_font span')
            if title_element is None:
                title_element = item.select_one('.list_font > span')
            model['title'] = title_element.text
            model['macro'] = True

            value_list = item.select('.nom_bg')
            for value in value_list:
                if '前值' in value.contents[0]:
                    model['former'] = value.contents[1].text
                elif '预期' in value.contents[0]:
                    model['predict'] = value.contents[1].text
                else:
                    raise Exception('数据错误')
            current_item = item.select_one(".zb_star")
            if '实际值' not in current_item.text:
                raise Exception('数据错误')
            model['current'] = current_item.select_one("em").text
        else:
            model['title'] = str.strip(title_item.text)
            href_item = title_item.select_one("a")
            if href_item is not None:
                model['url'] = href_item['href']

        # 加载图片
        image_list = item.select(".zb_pic img")
        for image in image_list:
            model['imageList'].append(image['src'])

        return model

    # 获取汇通网7*24数据
    @staticmethod
    def get_fx_live(date_str):
        result = []
        url = 'https://kx.fx678.com/date/' + date_str
        raw_html = get_response(url)
        parse_raw_html = get_parsed_href_html(url, raw_html)
        html = BeautifulSoup(parse_raw_html, 'html.parser')
        item_list = html.select(".body_zb_li")

        for item in item_list:
            date_item = item.select_one('.zb_time')
            if date_item is None:
                break
            date_time_str = date_str + " " + str.strip(date_item.text)
            if '快讯' in date_time_str:
                continue

            model = DataService.resolve_fx_live_item(item, date_time_str)
            result.append(model)

        # 解析置顶数据项
        top_item_list = html.select("#isTop > ul > li")
        for top_item in top_item_list:
            time_element = top_item.select_one(".fb_time")
            time_str = time_element.text
            date_time_str = date_str + ' ' + str.strip(time_str)
            model = DataService.resolve_fx_live_item(top_item, date_time_str)
            model['isTop'] = True
            result.append(model)

        return result

    # 提取概念板块所有的数据
    @staticmethod
    def get_concept_block_item_list():
        url = 'http://data.eastmoney.com/bkzj/gn.html'
        raw_html = get_response(url, encoding='gbk')
        parsed_raw_html = get_parsed_href_html(url, raw_html)
        html = BeautifulSoup(parsed_raw_html, 'html.parser')

        result = []

        for container_id in ['#pop-cont1', '#pop-cont2', '#pop-cont3']:
            cont_no = container_id[-1]
            if cont_no == '1':
                cont_name = '行业板块'
            elif cont_no == '2':
                cont_name = '概念板块'
            elif cont_no == '3':
                cont_name = '地区板块'
            else:
                cont_name = ''

            container = html.select_one(container_id)
            if container is None:
                raise Exception('找不到对应的板块')
            item_list = container.select("a")
            for item in item_list:
                code = item['href'].split('/')[-1].split('.')[0]
                secid = '90.' + code
                result.append({
                    "symbol": secid,
                    "code": code,
                    "name": item.text,
                    "type": 'concept',
                    "url": item['href'],
                    'block': cont_name
                })

        return result

    # 在 base 表中建立板块索引表
    @staticmethod
    def update_concept_block_index():
        concept_block_list = DataService.get_concept_block_item_list()
        for item in concept_block_list:
            base_document.update({ "type": 'concept', "symbol": item['symbol']}, item, True)


    @staticmethod
    def get_concept_block_history(code):
        url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
        params = {
            'cb': 'jQuery172002253503294348569_1576387811235',
            'secid': '90.' + code,
            'fields1': 'f1,f2,f3,f4,f5',
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
            "klt": 101,
            "fqt": 0,
            "beg": "20190101",
            "end": str(datetime.datetime.now().year + 1) + '0101',
            "_": 1576388830009
        }
        jsonp_response = get_response(url, params=params)
        response_json = extract_jsonp(jsonp_response, params['cb'])
        data_list = response_json['data']['klines']

        result = []
        for idx, item in enumerate(data_list):
            if idx == 0:
                continue
            last_item = data_list[idx - 1].split(',')
            today_item = data_list[idx].split(',')
            yesterday_close = float(last_item[2])
            today_close = float(today_item[2])
            model = {
                "date": today_item[0],
                "open": float(today_item[1]),
                "close": today_close,
                "max": float(today_item[3]),
                "min": float(today_item[4]),
                "volume": float(today_item[5]),
                "amount": float(today_item[6]),
                "percent": round((today_close - yesterday_close) / yesterday_close * 100, 2)
            }
            result.append(model)

        return result

    @staticmethod
    def get_gang_gu_tong_suspend_notice():
        url = 'http://www.sse.com.cn/services/hkexsc/disclo/announ/s_index.htm'
        notice_list = DataService.get_sse_official_site_notice(url)

        result = []
        for notice in notice_list:
            title = notice['title']
            if '交易日' in title or '休市' in title:
                result.append(notice)

        return result

    # 获取上交所官网公告
    @staticmethod
    def get_sse_official_site_notice(url):
        raw_html = get_response(url, method='POST')
        parsed_raw_html = get_parsed_href_html(url, raw_html)
        html = BeautifulSoup(parsed_raw_html, 'html.parser')
        item_list = html.select(".js_listPage dd")
        if len(item_list) == 0:
            raise Exception('找不到数据')
        result = []
        for item in item_list:
            current_date = str.strip(item.select_one("span").text)
            href_item = item.select_one("a")
            model = {
                "release_date": current_date,
                "title": str.strip(href_item['title']),
                "url": str.strip(href_item['href'])
            }
            model['id'] = model['url']
            result.append(model)

        return result

    @staticmethod
    def get_sse_suspend_notice():
        url = 'http://www.sse.com.cn/disclosure/announcement/general/s_index.htm'
        notice_list = DataService.get_sse_official_site_notice(url)

        result = []
        for notice in notice_list:
            title = notice['title']
            if '交易日' in title or '休市' in title:
                result.append(notice)

        return result

    # 获取相关市场的休市公告
    @staticmethod
    def get_suspend_notice():
        result = []
        result.extend(DataService.get_gang_gu_tong_suspend_notice())
        result.extend(DataService.get_sse_suspend_notice())

        return result

    # 获取财经日历
    @staticmethod
    def get_financial_event_calendar(_date):
        result = financial_calendar_document.find({ "source": 'fx678', "date": _date }, { "_id": 0 })
        return list(result)

    @staticmethod
    def get_recent_open_date_list():
        code = '1.000001'
        history = StockService.get_history_data(code)

        if history is None or len(history['data']) == 0:
            raise Exception('获取开市日期失败，数据为空')

        result = []
        for item in history['data']:
            result.append(item[0])

        return result

    # 获取同步数据的分时走势
    @staticmethod
    def get_sync_fragment_deal(secid, _date):
        sync_list = DataService.get_sync_item_list()
        for item in sync_list:
            if item['symbol'] == secid:
                return client.stock[item['document']].find_one({ "date": _date, "symbol": secid }, { "_id": 0 })

        return None

    @staticmethod
    def get_sync_item_list():
        sync_item_list = list(base_document.find({ "type": { '$in': ['index', 'concept', 'capital']}}))
        for item in sync_item_list:
            item['document'] = 'sync_' + item['type']

        return sync_item_list

    # 获取搜索项
    @staticmethod
    def get_search_option_list():
        result_model = {}
        item_list = base_document.find({}, { "symbol": 1, "name": 1, 'type': 1 })

        def get_type_label(val):
            if val == 'index':
                return '指数'
            elif val == 'concept':
                return '板块'
            elif val == 'capital':
                return '资金'
            else:
                return '股票'

        for item in item_list:
            _type = item['type']
            if _type not in result_model:
                result_model[_type] = {
                    "label": get_type_label(_type),
                    "value": _type,
                    "children": []
                }
            result_model[_type]['children'].append({
                "label": item['name'],
                "value": item['symbol']
            })

        result = []
        for key in result_model:
            result.append(result_model[key])

        return result

if __name__ == '__main__':
    # print(DataService().get_fx_live('2020-01-11'))
    # print(DataService.update_concept_block_index())
    print(DataService.get_search_option_list())