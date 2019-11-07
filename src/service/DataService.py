'''
    部分数据接口对接
'''
from src.utils.sessions import FuturesSession
from src.service.HtmlService import get_response
from src.utils import date
import json
from src.utils.date import get_english_month, get_ambiguous_date
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

        model = {
            "lastUpdateAt": get_ambiguous_date(get_english_month(date_text[-2]), int(date_text[-1])),
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


if __name__ == '__main__':
    DataService().get_stat_info()