'''
    部分数据接口对接
'''
from src.utils.sessions import FuturesSession
from src.service.HtmlService import get_response
from src.utils import date
import json

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


if __name__ == '__main__':
    DataService().get_stat_info()