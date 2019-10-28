from pymongo import MongoClient
from src.service.HtmlService import get_response, get_html_variable, extract_jsonp
import json

mongo_instance = MongoClient('mongodb://localhost:27017')

base_document = mongo_instance.stock.base
notice_document = mongo_instance.stock.notice
stock_pool_document = mongo_instance.stock.stock_pool
chinese_central_bank_base = 'http://www.chinamoney.com.cn'


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
                    "important": True,
                    "stock_name": base_model['name'],
                    "stock_code": code
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
                    "stock_name": base_model['name'],
                    "stock_code": code,
                    "title": risk['prefix'] + '_' + risk['title'],
                    "date": risk['releaseDate'],
                    "type": '债券风险提示',
                    "filterType": '债券',
                    "url": chinese_central_bank_base + risk['draftPath'],
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
                    "stock_name": base_model['name'],
                    "stock_code": code,
                    "title": publish_bond['bond_type_name'] + '_' + publish_bond['data']['name'],
                    "date": publish_bond['releaseDate'],
                    "url": chinese_central_bank_base + publish_bond['draftPath'],
                    "filterType": '债券',
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
            "type": item['ANN_RELCOLUMNS'][0]['COLUMNNAME'],
            "url": item['Url']
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

    # 获取股票竞价信息
    @staticmethod
    def get_stock_biding(code):

        def generate_biding_field_list(name_prefix, increment_base):
            field_list = []
            index_range = 5
            for index in range(index_range):
                base_index = 2 * index + 1
                field_list.append({
                    "name": name_prefix + str(index_range - index),
                    "fields": ['f' + str(increment_base + base_index), 'f' + str(increment_base + base_index + 1)]
                })
            return field_list

        total_field_list = []
        sell_field_list = generate_biding_field_list('卖', 30)
        buy_field_list = generate_biding_field_list('买', 10)
        buy_field_list.reverse()

        total_field_list += sell_field_list
        total_field_list += buy_field_list

        query_field_list = []
        for field_item in total_field_list:
            query_field_list += field_item['fields']

        url = 'http://push2.eastmoney.com/api/qt/stock/get'

        params = {
            "invt": 2,
            "fltt": 2,
            "secid": ('1.' if code[:2] == 'SH' else '0.') + code[2:],
            "fields": 'f43,f57,f58,f169,f170,f46,f44,f51,f168,f47,f164,f116,f60,f45,f52,f50,f48,f167,f117,f71,f161,f49,f530,f135,f136,f137,f138,f139,f141,f142,f144,f145,f147,f148,f140,f143,f146,f149,f55,f62,f162,f92,f173,f104,f105,f84,f85,f183,f184,f185,f186,f187,f188,f189,f190,f191,f192,f107,f111,f86,f177,f78,f110,f262,f263,f264,f267,f268,f250,f251,f252,f253,f254,f255,f256,f257,f258,f266,f269,f270,f271,f273,f274,f275,f127,f199,f128,f193,f196,f194,f195,f197,f80,f280,f281,f282,f284,f285,f286,f287',
            "cb": 'jQuery183047570304481979697_1571231187157',
            "_": "1571233484244"
        }

        raw_response = get_response(url, params=params)
        response = extract_jsonp(raw_response, params['cb'])
        data = response['data']
        result = {
            "current": data['f43'],
            "max": data['f44'],
            'min': data['f45'],
            "yesterday": data['f60'],
            "volume": data['f47'],
            "biding": []
        }
        for field_item in total_field_list:
            result['biding'].append([
                field_item['name'], data[field_item['fields'][0]], data[field_item['fields'][1]]
            ])

        return result

    # 获取公司的所有子公司
    @staticmethod
    def get_all_company(code):
        stock_base = base_document.find_one({"symbol": code})
        company_name_list = [
            stock_base['company']['org_name_cn']
        ]
        if 'sub_company_list' in stock_base:
            for sub_company in stock_base['sub_company_list']:
                if len(sub_company['company_name']) > 0:
                    company_name_list.append(sub_company['company_name'])

        return company_name_list

    # 获取所有的持股信息
    @staticmethod
    def get_all_stock_share_company(url):
        stock_holder_list = base_document.find({ 'stock_holder_list.company_href': url }, { "name": 1, "symbol": 1})
        result = []
        for stock in stock_holder_list:
            result.append({
                "code": stock['symbol'],
                "name": stock['name']
            })
        print(result)
        return result


if __name__ == '__main__':
    code = 'SZ002567'
    StockService.get_all_stock_share_company(code)