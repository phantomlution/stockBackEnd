from pymongo import MongoClient
from src.service.HtmlService import  get_response, get_html_variable

mongo_instance = MongoClient('mongodb://localhost:27017')

base_document = mongo_instance.stock.base
notice_document = mongo_instance.stock.notice
stock_pool_document = mongo_instance.stock.stock_pool


class StockService(object):

    @staticmethod
    def getMongoInstance():
        return mongo_instance

    # 加载预发布信息
    @staticmethod
    def update_stock_pre_release(code):
        url = 'http://data.eastmoney.com/stockdata/' + code[2:] + '.html'
        raw_html = get_response(url, encoding='gbk')

        variables = get_html_variable(raw_html, 'zdgzData')
        result = []

        for variable in variables:
            if 'sjlx' not in variable:
                raise Exception('字段变更')
            if variable['sjlx'] == '预约披露日':
                result.append(variable)

        base_document.update({"symbol": code}, {"$set": {"pre_release_list": result }}, True)

    # 加载预披露列表
    @staticmethod
    def load_pre_release_notice(code):
        result = []

        base_model = base_document.find_one({"symbol": code})
        if 'pre_release_list' in base_model:
            for release in base_model['pre_release_list']:
                result.append({
                    "title": release['sjlx'] + '_' + release['sjms'],
                    "date": release['rq'].split('T')[0],
                    "type": release['sjlx'],
                    "important": True
                })

        return result

    # 加载债券风险提示列表
    @staticmethod
    def load_bond_risk_notice(code):
        result = []
        base_model = base_document.find_one({"symbol": code})
        if 'bond_risk_list' in base_model:
            for risk in base_model['bond_risk_list']:
                result.append({
                    "title": risk['prefix'] + '_' + risk['title'],
                    "date": risk['releaseDate'],
                    "type": '债券风险提示',
                    "important": True
                })

        return result

    # 加载债券发行信息
    @staticmethod
    def load_bond_publish_notice(code):
        result = []
        base_model = base_document.find_one({"symbol": code})
        if 'bond_publish_list' in base_model:
            for publish_bond in base_model['bond_publish_list']:
                result.append({
                    "title": publish_bond['data']['bond_type_name'] + '_' + publish_bond['data']['name'],
                    "date": publish_bond['releaseDate'],
                    "type": '债券发行',
                    "important": True
                })

        return result

    # 加载公告
    @staticmethod
    def load_stock_notice(code):
        result = []
        # 聚合所有的公告，并且统一格式
        notice_item = notice_document.find_one({ "code": code[2:]})

        for notice in list(notice_item['data']):
            result.append({
                "title": notice['NOTICETITLE'],
                "date": notice['NOTICEDATE'].split('T')[0],
                "type": notice["ANN_RELCOLUMNS"][0]['COLUMNNAME']
            })

        result += StockService.load_pre_release_notice(code)
        result += StockService.load_bond_publish_notice(code)
        result += StockService.load_bond_risk_notice(code)

        return result

    # 加入股票池
    @staticmethod
    def add_stock_pool(model):
        code = model['code']

        # 手动更新预披露公告公告
        StockService.update_stock_pre_release(code)

        stock_pool_document.update({ "code": code }, model, True)

    # 删除
    @staticmethod
    def remove_stock_pool(code):
        stock_pool_document.remove({ "code": code })

    @staticmethod
    def get_stock_pool():
        return list(stock_pool_document.find({}, { "_id": 0 }))