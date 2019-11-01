'''
    专门用于做统计分析
'''
from src.service.StockService import StockService
from src.assets.DataProvider import DataProvider

client = StockService.getMongoInstance()
base_document = client.stock.base
history_document = client.stock.history


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
                    date_range = model['start'].split('-')
                    year = int(date_range[0])
                    month = int(date_range[1])
                    start_close = AnalyzeService.get_stock_price(model['code'], model['start'])
                    next_close = AnalyzeService.get_stock_price(model['code'], model['next'])
                    if start_close is not None and next_close is not None:
                        model['diff'] = (next_close - start_close) / start_close * 100
                    if year == 2019 and 'diff' in model:
                        result.append(model)
        print(result)





if __name__ == '__main__':
    AnalyzeService.analyze_profit_point()