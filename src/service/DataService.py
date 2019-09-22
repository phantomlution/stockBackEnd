'''
    部分数据接口对接
'''
from src.utils.sessions import FuturesSession
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
