from src.utils.date import getCurrentTimestamp, get_ambiguous_date, get_current_date_str
from src.service.HtmlService import get_response, extract_jsonp
from src.service.AuthService import AuthService
import datetime
from src.utils.lodash import lodash
import json
from src.utils.DataUtils import DataUtils

FREQUENCY_ONE_MINUTE = '1min'

YEAR_AFTER_NEXT_YEAR = datetime.datetime.now().year + 2


class EastMoneyService:

    @staticmethod
    def get_response(url, params):
        current = str(getCurrentTimestamp())

        # 自动追加jsonp
        params['cb'] = 'jQuery' + '1124040880950532178506' + '_' + current
        params['_'] = current

        jsonp_response = get_response(url, params=params)
        json_response = extract_jsonp(jsonp_response, params['cb'])

        return {
            "code": 200,
            "data": json_response['data']
        }

    # 将源数据按照某一天的间隔进行归并
    @staticmethod
    def group_by_day(secid, name, item_list, callback):
        result = []
        model = None

        kline = EastMoneyService.get_kline(secid)

        for trend in item_list:
            item = trend.split(',')
            _date = item[0].split(' ')[0]
            _time = item[0].split(' ')[1]

            if model is not None and model['date'] != _date:
                if len(model['data']) > 0:
                    result.append(model)
                model = None

            current = callback(_time, item)

            if model is None:
                model = {
                    "secid": secid,
                    "date": _date,
                    "name": name,
                    "data": []
                }
                # 拼接昨收
                idx = lodash.find_index(kline, lambda _item: _item['date'] == _date)
                if idx == -1:
                    raise Exception('找不到pre_close')
                elif idx == 0:
                    # 第一个点
                    model['pre_close'] = kline[idx]['open']
                else:
                    model['pre_close'] = kline[idx - 1]['close']

            model['data'].append(current)

        if len(model['data']) > 0:
            result.append(model)

        return result

    # 提取指数或者概念板块的当天走势
    @staticmethod
    def get_index_or_concept_one_minute_tick_data(secid, days=1):
        if days > 5:
            raise Exception('最多只能获取5天')
        url = 'http://push2his.eastmoney.com/api/qt/stock/trends2/get'
        params = {
            'secid': secid,
            'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11',
            'fields2': 'f51,f53,f56,f58',
            'iscr': '0',
            'ndays': days
        }

        response = EastMoneyService.get_response(url, params)

        data = response['data']

        trends_list = data['trends']

        name = data['name']

        def callback(_time, item):
            return {
                "time": _time,
                "price": float(item[1]),
                "amount": float(item[2])

            }

        result = EastMoneyService.group_by_day(secid, name, trends_list, callback)

        return result

    # 获取K线数据
    @staticmethod
    def get_kline(secid):
        url = 'http://push2his.eastmoney.com/api/qt/stock/kline/get'
        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
            "klt": "101",
            "fqt": "0",
            "beg": "19900101",
            "end": str(YEAR_AFTER_NEXT_YEAR) + "0101"
        }

        response = EastMoneyService.get_response(url, params=params)

        kline_list = response['data']['klines']

        result = []

        for kline_item in kline_list:
            item = kline_item.split(',')
            model = {
                "date": item[0],
                "open": float(item[1]),
                "close": float(item[2]),
                "max": float(item[3]),
                "min": float(item[4]),
                "amount": float(item[6])
            }
            result.append(model)

        DataUtils.generate_pre_close(result)

        return result[-420:]

    @staticmethod
    def _get_hot_money_data():

        url = 'http://push2.eastmoney.com/api/qt/kamt.rtmin/get'
        params = {
            "fields1": "f1,f2,f3,f4",
            "fields2": "f51,f52,f53,f54,f55,f56",
        }

        response_json = EastMoneyService.get_response(url, params=params)
        if 'data' not in response_json:
            raise Exception('[北向资金]数据异常')

        data = response_json['data']

        data['date'] = get_current_date_str()
        return data

    # 获取资金K线（每日数据的净买入= 成交 + 挂单，不太准）
    @staticmethod
    def resolve_hot_money(key, raw):
        '''
            s2n: 北向资金
                0. 时间点
                1. 沪股通流入金额
                2. 沪股通余额
                3. 深股通流入金额
                4. 深股通余额

            n2s: 南向资金
                0. 时间点
                1. 港股通(沪)流入金额
                2. 港股通(沪)余额
                3. 港股通(深)流入金额
                4. 港股通(深)余额
        '''

        target_date_str = raw[key + 'Date']

        month = int(target_date_str.split('-')[0])
        day = int(target_date_str.split('-')[1])

        actual_date = get_ambiguous_date(month, day)

        point_list = raw[key]

        result = []
        for point in point_list:
            item = point.split(',')
            time = item[0]
            if len(time.split(':')[0]) == 1:
                time = '0' + time
            if item[1] == '-':
                continue
            result.append({
                "time": time,
                "huAmount": int(float(item[1]) * 10000),
                "huRemain": int(float(item[2]) * 10000),
                "shenAmount": int(float(item[3]) * 10000),
                "shenRemain": int(float(item[4]) * 10000)
            })
        return {
            "date": actual_date,
            "data": result
        }

    @staticmethod
    def get_latest_hot_money_data(secid):
        raw_data = EastMoneyService._get_hot_money_data()
        if secid == 'CAPITAL.NORTH':
            return EastMoneyService.resolve_hot_money('s2n', raw_data)
        elif secid == 'CAPITAL.SOUTH':
            return EastMoneyService.resolve_hot_money('n2s', raw_data)
        else:
            raise Exception('类型错误')

    @staticmethod
    def get_hot_money_page(market_type, page_no=1, page_size=200):
        one_million = 100 * 10000
        url = 'http://dcfm.eastmoney.com/EM_MutiSvcExpandInterface/api/js/get'
        params = {
            "type": "HSGTHIS",
            "filter": "(MarketType=" + str(market_type) + ")",
            "js": '{"data":(x),"pages":(tp)}',
            'ps': page_size,
            'p': page_no,
            'token': AuthService.get_east_money_token(),
            'sr': -1,
            'st': 'DetailDate',
            'rt': "52625022"
        }
        response = get_response(url, params=params)
        response_json = json.loads(response)
        result = []
        for item in response_json['data']:
            model = {
                "date": item['DetailDate'].split('T')[0],
                'pre_close': (item['LSZJLR'] - item['DRCJJME']) * one_million,
                "amount": (item['MRCJE'] + item['MCCJE']) * one_million
            }
            result.append(model)
        return result

    @staticmethod
    def get_hu_gu_tong_hot_money():
        return EastMoneyService.get_hot_money_page('1')

    @staticmethod
    def get_shen_gu_tong_hot_money():
        return EastMoneyService.get_hot_money_page('3')

    @staticmethod
    def get_gang_gu_tong_hu_hot_money():
        return EastMoneyService.get_hot_money_page('2')

    @staticmethod
    def get_gang_gu_tong_shen_hot_money():
        return EastMoneyService.get_hot_money_page('4')



if __name__ == '__main__':
    # print(EastMoneyService.get_index_or_concept_one_minute_tick_data('1.000001', days=5))
    # print(EastMoneyService.get_latest_hot_money_north())
    # print(EastMoneyService.get_kline('1.000001'))
    # print(EastMoneyService.get_kline('1.601658'))
    print(EastMoneyService.get_hot_money_page(page_no=1))