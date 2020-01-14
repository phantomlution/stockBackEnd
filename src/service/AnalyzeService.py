'''
    专门用于做统计分析
'''
from src.service.StockService import StockService
from src.service.FinancialService import get_history_fragment_trade_data
from src.utils.FileUtils import generate_static_dir_file
from src.utils.date import getCurrentTimestamp, date_str_to_timestamp, full_time_format
from src.service.DatabaseService import DatabaseService
import os
import json
import bson
import math
from src.utils.lodash import lodash

client = StockService.getMongoInstance()
base_document = client.stock.base
history_document = client.stock.history
stunt_document = client.stock.stunt
concept_block_ranking_document = client.stock.concept_block_ranking
surge_for_short_document = client.stock.surge_for_short
analyze_stock_document = client.stock.analyze_stock


def generate_analyze_file(file_name, content):
    return generate_static_dir_file('analyze' + os.sep + file_name, json.dumps(content))


class AnalyzeService:

    @staticmethod
    def analyze_restrict_date():
        stock_list = base_document.find({}, { 'restrict_sell_list': 1, "symbol": 1 })
        date_map = {}
        for stock in stock_list:
            code = stock['symbol']
            if 'restrict_sell_list' not in stock:
                continue
            restrict_sell_list = stock['restrict_sell_list']
            for restrict_sell_item in restrict_sell_list:
                if restrict_sell_item['increment'] == 0 or '首发' in restrict_sell_item['desc']:
                    continue

                date = restrict_sell_item['date']

                if date not in date_map:
                    date_map[date] = []
                date_map[date].append(code)

        result = []
        for date in date_map:
            result.append({
                "date": date,
                "itemList": date_map[date]
            })

        return result

    @staticmethod
    def get_stock_price(code, date):
        history_data = history_document.find_one({"code": code })
        for item in history_data['data']:
            if item[0] == date:
                return item[2]
        return None

    # 通过解禁日期去计算盈利点
    @staticmethod
    def analyze_profit_point():
        result = []
        stock_list = StockService.get_stock_list()
        for stock in stock_list:
            stock_base = StockService.get_stock_base(stock['code'])
            code = stock_base['symbol']
            restrict_sell_list = stock_base['restrict_sell_list']
            for idx, restrict_sell in enumerate(restrict_sell_list):
                if idx == 0:
                    continue
                diff = restrict_sell_list[idx]['timestamp'] - restrict_sell_list[idx - 1]['timestamp']
                if diff < 62 * 24 * 60 * 60 * 1000:
                    model = {
                        "code": code,
                        "name": stock_base['name'],
                        "start": restrict_sell_list[idx - 1]['date'],
                        "next": restrict_sell_list[idx]['date']
                    }
                    model['desc'] = model['start'] + ', ' + model['next']
                    date_range = model['start'].split('-')
                    year = int(date_range[0])
                    month = int(date_range[1])
                    start_close = AnalyzeService.get_stock_price(model['code'], model['start'])
                    next_close = AnalyzeService.get_stock_price(model['code'], model['next'])
                    if start_close is not None and next_close is not None:
                        model['diff'] = (next_close - start_close) / start_close * 100
                    if year == 2019 and 'diff' in model:
                        result.append(model)

        generate_analyze_file('二次限售解禁分析.json', result)


    @staticmethod
    def get_price_break_point():
        result= []
        stock_list = StockService.get_stock_list()
        # stock_list = [{
        #     "code": 'SH600242'
        # }]
        for stock in stock_list:
            result += AnalyzeService.get_price_break_point_by_code(stock["code"])

        final_result = []
        for item in result:
            for desc in item['desc']:
                date = desc.split(' ')[0]
                final_result.append({
                    "code": item['code'],
                    "date": date
                })

        final_result = sorted(final_result, key=lambda sub_item: sub_item["date"], reverse=True)
        print(final_result)

    # 获取涨停板的次数
    @staticmethod
    def get_ceil_close_count(data_list):
        count = 0
        threshold_percent = 9.8
        for idx, item in enumerate(data_list):
            if idx == 0:
                continue
            yesterday_item = data_list[idx - 1]
            today_item = data_list[idx]
            if ((today_item[2] - yesterday_item[2]) / yesterday_item[2] * 100) >= threshold_percent:
                count += 1

        return count


    # 获取开板点
    @staticmethod
    def get_price_break_point_by_code(code):
        def get_diff_percent(start, end):
            return math.fabs((start - end) * 100 / end)
        threshold_percent = 9.8

        history = history_document.find_one({ "code": code })
        result = []
        if history is not None:
            desc_list = []
            analyze_history = history['data']
            for idx, item in enumerate(analyze_history):
                if idx == 0:
                    continue
                yesterday_item = analyze_history[idx - 1]
                today_item = analyze_history[idx]
                yesterday = yesterday_item[2]
                close = today_item[2]
                max_price = today_item[3]
                min_price = today_item[4]
                close_diff_percent = get_diff_percent(close, yesterday)
                max_diff_percent = get_diff_percent(max_price, yesterday)
                min_diff_percent = get_diff_percent(min_price, yesterday)

                # if max_diff_percent > threshold_percent and close_diff_percent <= threshold_percent:
                #     desc_list.append(today_item[0] + " 涨停开板")
                # if min_diff_percent >= threshold_percent and close_diff_percent < threshold_percent:
                if True:
                    if idx > 30:
                        last_month_trade_list = analyze_history[idx - 1 - 30:idx - 1]
                        ceil_close_count = AnalyzeService.get_ceil_close_count(last_month_trade_list)
                        if ceil_close_count > 1:
                            next_month_trade_list = analyze_history[idx: idx + 60]
                            if len(last_month_trade_list) > 0 and len(next_month_trade_list) > 0:
                                sorted_last_month_trade_list = sorted(last_month_trade_list, key=lambda biding: biding[2])
                                sorted_next_month_trade_list = sorted(next_month_trade_list, key=lambda biding: biding[2])
                                max_close = sorted_last_month_trade_list[-1][2]
                                min_close = sorted_next_month_trade_list[0][2]
                                if ((max_close - min_close) / max_close) * 100 >= 60:
                                    desc_string = sorted_next_month_trade_list[0][0] + ' 类跌停'
                                    if desc_string not in desc_list:
                                        desc_list.append(desc_string)
            if len(desc_list) > 0:
                result.append({
                    "code": code,
                    "desc": desc_list
                })

        return result

    @staticmethod
    def get_stunt_point_list():
        result = []
        stunt_list = stunt_document.find({}, { "_id": 0 })
        for stunt in stunt_list:
            filter_stunt = []
            original_stunt = stunt['point']
            for item in original_stunt:
                if '15:00' in item['time']:
                    continue
                if item['price'] / item['yesterday'] > 1.05:
                    continue
                if item['price'] / item['yesterday'] < 0.95:
                    continue
                filter_stunt.append(item)
            if len(filter_stunt) > 0:
                stunt['list'] = filter_stunt
                result.append(stunt)

        return result

    @staticmethod
    def get_low_amount_restrict_sell():
        stock_list = StockService.get_stock_list()

        current = getCurrentTimestamp() + 1 * 24 * 60 * 60 * 1000
        latest = current - 90 * 24 * 60 * 60 * 1000

        result = []
        count = 0
        for stock in stock_list:
            code = stock['code']
            count += 1
            print(count)

            base = StockService.get_stock_base(code)
            if 'restrict_sell_list' not in base:
                continue
            sell_list = base['restrict_sell_list']
            filter_sell_list = list(filter(lambda item: current >= item['timestamp'] >= latest, sell_list))
            if len(filter_sell_list) == 0:
                continue
            history_data = DatabaseService.get_history_data(code)
            point_list = []
            for sell_item in filter_sell_list:
                # 计算近30日平均成交量
                early_history_data = list(filter(lambda item: item[0] <= sell_item['date'], history_data))
                if len(early_history_data) < 30:
                    raise Exception('error')

                total = 0
                specified_range = early_history_data[-30:]
                for data in specified_range:
                    amount = data[6]
                    total += amount
                average = total / len(specified_range)
                average_in_million = average / 1000 / 1000
                if average_in_million < 20:
                    point_list.append({
                        "date": sell_item['date'],
                        "amount_in_M": round(average_in_million, 2)
                    })

            if len(point_list) > 0:
                result.append({
                    "code": stock['code'],
                    "name": stock['name'],
                    'list': point_list
                })

        return result

    @staticmethod
    def get_concept_block_ranking():
        result = concept_block_ranking_document.find({}, {"_id": 0})
        return list(result)

    # 判断是否存在，跌-拉高出货
    @staticmethod
    def analyze_surge_for_short(code, date):
        trade_point_list = get_history_fragment_trade_data(code, date)

        if trade_point_list is None or len(trade_point_list) == 0:
            raise Exception('{},{}找不到分时成交数据'.format(code, date))

        yesterday_close = trade_point_list[0]['price'] + trade_point_list[0]['change']

        # 中场休息时间
        rest_timestamp = date_str_to_timestamp(date + ' 12:00:00', full_time_format)

        def get_virtual_timestamp(timestamp):
            if timestamp > rest_timestamp:
                return timestamp - 90 * 60 * 1000 - 10
            else:
                return timestamp

        for point in trade_point_list:
            point['timestamp'] = date_str_to_timestamp(date + ' ' + point['time'], full_time_format)

        temp_max_item = lodash.max_by(trade_point_list, lambda item: item['price'])

        # 可能存在多个相同的最大值
        max_item_list = list(filter(lambda item: item['price'] == temp_max_item['price'], trade_point_list))

        if len(max_item_list) == 0:
            return None

        # 只考虑最后一个最大值
        max_item = max_item_list[-1]

        def left_filter_rule(item):
            item_timestamp = get_virtual_timestamp(item['timestamp'])
            max_item_timestamp = get_virtual_timestamp(max_item['timestamp'])
            return item_timestamp <= max_item_timestamp and (max_item_timestamp - item_timestamp) < 10 * 60 * 1000

        def right_filter_rule(item):
            item_timestamp = get_virtual_timestamp(item['timestamp'])
            max_item_timestamp = get_virtual_timestamp(max_item['timestamp'])
            return item_timestamp >= max_item_timestamp and (item_timestamp - max_item_timestamp) < 3 * 10 * 60 * 1000

        left_point_list = list(filter(left_filter_rule, trade_point_list))
        right_point_list = list(filter(right_filter_rule, trade_point_list))

        # 找到左侧数据点中的最小值
        left_min_item = lodash.min_by(left_point_list, lambda item: item['price'])
        left_min_increment = lodash.diff_in_percent(left_min_item['price'], yesterday_close)

        # 找到右侧数据中的最小值
        right_min_item = lodash.min_by(right_point_list, lambda item: item['price'])
        right_min_increment = lodash.diff_in_percent(right_min_item['price'], yesterday_close)

        max_item_increment = lodash.diff_in_percent(max_item['price'], yesterday_close)

        surge_percent = max_item_increment - left_min_increment
        fall_percent = max_item_increment - right_min_increment

        if surge_percent >= 3 and fall_percent >= 1:
            return {
                "date": date,
                "time": max_item['time'],
                "surge": surge_percent,
                "fall": fall_percent
            }

        return None

    @staticmethod
    def get_surge_for_short(code, date):
        item = surge_for_short_document.find_one({ "code": code, "date": date }, { "_id": 0})
        if item is None:
            # 如果提取不到数据，默认为 None
            try:
                result = AnalyzeService.analyze_surge_for_short(code, date)
            except Exception as e:
                print(e)
                result = None

            if result is None:
                time = ''
            else:
                time = result['time']
            model = {
                "code": code,
                "date": date,
                "time": time,
                "desc": '',
                "check": False,  # 是否人工确定
                "result": result
            }
            surge_for_short_document.insert(model)

        item = surge_for_short_document.find_one({ "code": code, "date": date })
        if item is None:
            raise Exception('找不到分析结果')

        item['_id'] = str(item['_id'])
        return item

    @staticmethod
    def update_surge_for_short(params):
        _id = params['id']
        _date = params['date']
        _code = params['code']
        _time = params['time']
        _desc = params['desc']
        _checked = params['check']

        # 强确认 _id, _date, _code 的匹配性
        item = surge_for_short_document.find_one({ "_id": bson.ObjectId(_id) })

        if item is None:
            raise Exception('找不到对应数据')

        if item['date'] != _date or item['code'] != _code:
            raise Exception('数据不匹配')

        update_model = {
            'time': _time,
            'desc': _desc,
            'check': _checked
        }
        surge_for_short_document.update({ "_id": bson.ObjectId(_id)}, { '$set': update_model })

    # 插入股票代码到临时表
    @staticmethod
    def update_stock_list(stock_list):
        analyze_stock_document.drop()
        for stock in stock_list:
            analyze_stock_document.insert(stock)

    @staticmethod
    def get_stock_list():
        return list(analyze_stock_document.find({}, { "_id": 0 }))

    @staticmethod
    def get_market_surge_for_short(date_list):
        result = []

        for _date in date_list:
            model = {
                "date": _date,
                "total": 0,
                "short": []
            }
            item_list = surge_for_short_document.find({ "date": _date }, { "_id": 0 })
            for item in item_list:
                if item['result'] is not None:
                    model['short'].append(item)
                model['total'] += 1

            if model['total'] == 0:
                continue

            result.append(model)

        return result


if __name__ == '__main__':
    print(AnalyzeService.analyze_surge_for_short('600242', '2019-12-23'))
