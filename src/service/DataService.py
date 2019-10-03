'''
    部分数据接口对接
'''
from src.utils.sessions import FuturesSession
from src.utils import date
import json

session = FuturesSession(max_workers=1)


class DataService(object):

    # 获取农产品指数
    @staticmethod
    def get_farm_product_index(code):
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