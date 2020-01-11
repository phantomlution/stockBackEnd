from pymongo import MongoClient
from src.service.HtmlService import get_response, get_html_variable, extract_jsonp
from src.utils.date import date_str_to_timestamp, getCurrentTimestamp
from src.service.EastMoneyService import EastMoneyService
import json

mongo_instance = MongoClient('mongodb://localhost:27017')

base_document = mongo_instance.stock.base
notice_document = mongo_instance.stock.notice
history_document = mongo_instance.stock.history
stock_pool_document = mongo_instance.stock.stock_pool
chinese_central_bank_base = 'http://www.chinamoney.com.cn'
ten_thousand = 10000


class StockService:

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

        if variables is not None:
            for variable in variables:
                if 'sjlx' not in variable:
                    raise Exception('字段变更')
                if variable['sjlx'] == '预约披露日':
                    result.append(variable)
                elif variable['sjlx'] == '限售解禁日':
                    result.append(variable)

        base_document.update({"symbol": code}, {"$set": {"pre_release_list": result }}, True)

    # 加载预披露列表
    @staticmethod
    def load_pre_release_notice(code):
        result = []

        base_model = base_document.find_one({"symbol": code})
        if base_model is not None:
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

    @staticmethod
    def get_stock_base(code):
        return base_document.find_one({ "symbol": code }, { "_id": 0 })

    # 加载债券风险提示列表
    @staticmethod
    def load_bond_risk_notice(code):
        result = []
        base_model = StockService.get_stock_base(code)
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
        base_model = StockService.get_stock_base(code)
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
        base = StockService.get_stock_base(code)
        model['name'] = base['name']
        model['is_delete'] = False
        if model['order'] is None:
            model['order'] = 999

        if StockService.get_stock_pool_item(code) is None:
            # 手动更新预披露公告公告
            StockService.update_stock_pool_item_info(code)

        stock_pool_document.update({ "code": code }, model, True)

    @staticmethod
    def get_stock_pool_item(code):
        return stock_pool_document.find_one({ "code": code }, { "_id": 0 })

    # 删除
    @staticmethod
    def remove_stock_pool(code):
        stock_pool_document.update({"code": code}, { '$set': { "is_delete": True } })

    @staticmethod
    def get_stock_pool():

        item_list_cursor = stock_pool_document.aggregate([
            {
                '$match': {
                    'is_delete': False
                }
            },
            {
                '$lookup': {
                    "localField": "code",
                    "from": "base",
                    "foreignField": "symbol",
                    "as": "base"
                }
            },
            {
              '$unwind': '$base'
            },
            {
                "$sort": {
                    "order": 1
                }
            },
            {
                "$project": {
                    "_id": 0,
                    'base._id': 0
                }
            }
        ])
        return list(item_list_cursor)

    @staticmethod
    def get_notice_list(code):
        return list(notice_document.find({ "stock_code": code }, { "_id" : 0 }))

    @staticmethod
    def parse_stock_notice_item(item):
        market_name = item['CDSY_SECUCODES'][0]['TRADEMARKET']
        if '深交所' in market_name or '深圳证券' in market_name:
            prefix = 'SZ'
        elif '上交所' in market_name or '上海证券' in market_name:
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
            "open": data['f46'],
            "max": data['f44'],
            'min': data['f45'],
            "yesterday": data['f60'],
            "volume": data['f47'],
            "amount": data['f48'],
            'turnOverRate': data['f168'],
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
        return result

    @staticmethod
    def get_all_restricted_sell_stock(result, code, page=1, page_size=20):
        query_code = code[2:]
        url = 'http://dcfm.eastmoney.com/em_mutisvcexpandinterface/api/js/get'
        params = {
            "token": "70f12f2f4f091e459a279469fe49eca5",
            "st": "ltsj",
            "sr": -1,
            "p": page,
            "ps": page_size,
            "type": "XSJJ_NJ_PC",
            "js": '{"pages":(tp),"data":(x),"font":(font)}',
            "filter": "(gpdm='" + query_code + "')",
            "rt": 52416643
        }

        raw_response = get_response(url, params=params)
        response = json.loads(str(raw_response))
        font_mapping = response['font']['FontMapping']

        def parse_font(raw):
            font_result = raw
            for font_map in font_mapping:
                font_result = font_result.replace(font_map['code'], str(font_map['value']))

            return int(float(font_result) * 10000)

        for item in response['data']:
            date = item['ltsj'].split('T')[0]
            result.append({
                "date": date,
                "increment": parse_font(item['jjsl']),
                "timestamp": date_str_to_timestamp(date),
                "desc": item['xsglx']
            })

        if len(response['data']) < page_size:
            return result
        else:
            return StockService.get_all_restricted_sell_stock(result, code, page + 1, page_size)

    # 获取限售股票
    @staticmethod
    def update_stock_restricted_sell(code):
        restrict_sell_list = []
        StockService.get_all_restricted_sell_stock(restrict_sell_list, code)
        restrict_sell_list.reverse()
        base_document.update({"symbol": code}, {'$set': {'restrict_sell_list': restrict_sell_list}}, True)


    # 获取概念板块资金流向
    @staticmethod
    def get_concept_block():
        url = 'http://51.push2.eastmoney.com/api/qt/clist/get'
        params = {
            "cb": "jQuery112407684244893231433_1575458086176",
            "pn": 1,
            "pz": 20,
            "po": 1,
            "np": 1,
            "fltt": 2,
            "invt": 2,
            "fid": "f3",
            "fs": "m:90 t:3",
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152,f124,f107,f104,f105,f140,f141,f207,f222"
        }

        response = get_response(url, params=params)
        response_json = extract_jsonp(response, params['cb'])
        concept_list = []
        for item in response_json['data']['diff']:
            concept_list.append({
                "name": item['f14'],
                "url": "http://quote.eastmoney.com/web/" + item["f12"] + ".html",
                "percent": item['f3'],
                "rise": item['f104'],
                "fall": item['f105']
            })

        return concept_list

    @staticmethod
    def get_history_data(code):
        item = history_document.find_one({"symbol": code}, {"_id": 0})
        if item is None:
            return None
        return item['list']

    @staticmethod
    def update_stock_pool_item_info(code):
        StockService.update_stock_pre_release(code)
        StockService.update_stock_restricted_sell(code)

    @staticmethod
    def get_stock_real_time_trend(code):
        url = 'http://push2.eastmoney.com/api/qt/stock/trends2/get'
        current = getCurrentTimestamp()
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
            "ndays": "1",
            "iscr": "0",
            "secid": ("1" if code[:2] == 'SH' else "0") + "." + code[2:],
            "cb": "jQuery112409088551039429049_" + str(current),
            "_": str(current),
        }
        raw_response = get_response(url, params=params)
        response_json = extract_jsonp(raw_response, params['cb'])['data']
        trend_data = response_json['trends']

        result = []
        for item in trend_data:
            raw_data = item.split(',')
            result.append({
                "time": raw_data[0].split(' ')[1] + ':00',
                "price": raw_data[2]
            })

        return result

    @staticmethod
    def get_all_item():
        return list(base_document.find())


if __name__ == '__main__':
    # result = StockService.get_hot_money_south()
    # print(result)
    # print('')
    hot_money_document = mongo_instance.stock.hotMoney
    item = hot_money_document.find_one({ "date": '2019-12-24'})
    result = EastMoneyService.resolve_hot_money('n2s', item)
    result['symbol'] = 'CAPITAL.SOUTH'
    result['type'] = 'capital'
    mongo_instance.stock.sync_capital.insert(result)
    print(result)