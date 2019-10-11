from pymongo import MongoClient
from src.service.HtmlService import  get_response, get_html_variable
import json

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
        result += StockService.get_notice_list(code)
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

    @staticmethod
    def get_notice_list(code):
        return list(notice_document.find({ "stock_code": code }, { "_id" : 0 }))

    @staticmethod
    def parse_stock_notice_item(item):
        market_name = item['CDSY_SECUCODES'][0]['TRADEMARKET']
        if '深交所' in market_name:
            prefix = 'SZ'
        elif '深圳证券' in market_name:
            prefix = 'SZ'
        elif '上交所' in market_name:
            prefix = 'SH'
        elif '香港交易所' in market_name:
            return None
        elif '中国银行' in market_name:
            return None
        else:
            raise Exception('市场错误: {}'.format(market_name))

        model = {
            "notice_id": item['INFOCODE'],
            "date": item['NOTICEDATE'].split('T')[0],
            'attach_type': item['ATTACHTYPE'],
            'attach_size': item['ATTACHSIZE'],
            'title': item['NOTICETITLE'],
            'stock_code': prefix + item['CDSY_SECUCODES'][0]['SECURITYCODE'],
            "stock_name": item['CDSY_SECUCODES'][0]['SECURITYFULLNAME'],
            "market": market_name,
            "type": item['ANN_RELCOLUMNS'][0]['COLUMNNAME']
        }

        return model

    # 获取质押比例
    @staticmethod
    def get_pledge_rate(code):
        url = 'http://data.eastmoney.com/DataCenter_V3/gpzy/chart.aspx'
        params = {
            "t": 1,
            "scode": code[2:]
        }

        response = get_response(url, params=params)
        response_json = json.loads(response)
        pledge_list = response_json['MoreData']
        if len(pledge_list) == 0:
            return 0
        else:
            return pledge_list[0]['value']

    # 获取股票增减持公告
    @staticmethod
    def get_stock_notice_change(code):
        url = 'http://data.eastmoney.com/notices/getdata.ashx'
        params = {
            "StockCode": code[2:],
            "CodeType": 1,
            "PageIndex": 1,
            "PageSize": 50,
            "jsObj": "qnMihhKR",
            "SecNodeType": 0,
            "FirstNodeType": 7,
            "rt": 52358670
        }

        raw_response = get_response(url, params=params)
        raw_json_str = raw_response[raw_response.index('=') + 1 : raw_response.rindex('}') + 1]
        response_json = json.loads(raw_json_str)
        result = []
        for item in response_json['data']:
            parsed_model = StockService.parse_stock_notice_item(item)
            if parsed_model is not None:
                result.append(parsed_model)

        return result