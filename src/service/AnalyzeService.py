'''
    专门用于做统计分析
'''
from src.service.StockService import StockService

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


if __name__ == '__main__':
    AnalyzeService.analyze_restrict_date()