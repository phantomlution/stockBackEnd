from src.utils.date import getCurrentTimestamp
from src.service.HtmlService import get_response, extract_jsonp
import datetime
from src.utils.lodash import lodash

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

    # 获取上证指数
    @staticmethod
    def get_latest_shanghai_composite_index():
        result = EastMoneyService.get_index_or_concept_one_minute_tick_data('1.000001')
        return result

    # 获取概念板块数据
    @staticmethod
    def get_latest_concept_block_data(code):
        secid = '90.' + code
        result = EastMoneyService.get_index_or_concept_one_minute_tick_data(secid)
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

        for kline_item in kline_list[-420:]:
            item = kline_item.split(',')
            result.append({
                "date": item[0],
                "open": float(item[1]),
                "close": float(item[2]),
                "max": float(item[3]),
                "min": float(item[4]),
                "amount": float(item[6])
            })

        return result

if __name__ == '__main__':
    print(EastMoneyService.get_index_or_concept_one_minute_tick_data('1.000001', days=5))

    # print(EastMoneyService.get_kline('1.000001'))
