'''
    部分数据接口对接
'''
from src.utils.sessions import FuturesSession
from src.service.HtmlService import get_response, get_absolute_url_path, get_parsed_href_html
from src.utils import date
import json
from src.utils.date import get_english_month, get_ambiguous_date, full_time_format, parse_date_str, date_obj_to_timestamp
from bs4 import BeautifulSoup

session = FuturesSession(max_workers=1)


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
                raise Exception('数据异常')

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
            model['title'] = item.select_one(".zb_font span").text
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
        top_item_list = html.select("#isTop li")
        for top_item in top_item_list:
            time_str = top_item.select_one(".fb_time").text
            date_time_str = date_str + ' ' + str.strip(time_str)
            model = DataService.resolve_fx_live_item(top_item, date_time_str)
            model['isTop'] = True
            result.append(model)

        return result


if __name__ == '__main__':
    print(DataService().get_fx_live('2019-11-14'))