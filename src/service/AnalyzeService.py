'''
    专门用于做统计分析
'''
from src.service.StockService import StockService
from src.assets.DataProvider import DataProvider
from src.utils.FileUtils import generate_static_dir_file
import os
import json
import math

client = StockService.getMongoInstance()
base_document = client.stock.base
history_document = client.stock.history


def generate_analyze_file(file_name, content):
    return generate_static_dir_file('analyze' + os.sep + file_name, json.dumps(content))


class AnalyzeService:

    @staticmethod
    def analyze_restrict_date():
        stock_list = base_document.find({}, { 'restrict_sell_list': 1, "symbol": 1 })
        date_map = {}
        for stock in stock_list:
            code = stock['symbol']
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
        stock_list = DataProvider().get_stock_list()
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
        stock_list = DataProvider().get_stock_list()
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







if __name__ == '__main__':
    AnalyzeService.get_price_break_point()