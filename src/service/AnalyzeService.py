'''
    专门用于做统计分析
'''
from src.service.StockService import StockService
from src.assets.DataProvider import DataProvider

client = StockService.getMongoInstance()
base_document = client.stock.base


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

    # 通过解禁日期去计算盈利点
    @staticmethod
    def analyze_profit_point():
        stock_list = DataProvider().get_stock_list()
        for stock in stock_list:
            stock_base = StockService.get_stock_base(stock['code'])
            restrict_sell_list = stock_base['restrict_sell_list']
            for idx, restrict_sell in enumerate(restrict_sell_list):
                if idx == 0:
                    continue
                diff = restrict_sell_list[idx]['timestamp'] - restrict_sell_list[idx - 1]['timestamp']
                if diff < 62 * 24 * 60 * 60 * 1000:
                    model = {
                        "code": stock_base['symbol'],
                        "name": stock_base['name'],
                        "start": restrict_sell_list[idx - 1]['date'],
                        "next": restrict_sell_list[idx]['date']
                    }
                    date_range = model['start'].split('-')
                    year = int(date_range[0])
                    month = int(date_range[1])
                    if year == 2019:
                        print(model)






if __name__ == '__main__':
    AnalyzeService.analyze_profit_point()