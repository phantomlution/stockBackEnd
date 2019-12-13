'''
    股票交易量分析
'''
from src.script.job.Job import Job
from src.service.FinancialService import get_history_fragment_trade_data
from src.service.StockService import StockService
from src.assets.DataProvider import DataProvider
import asyncio

client = StockService.getMongoInstance()
stunt_document = client.stock.stunt


class StockVolumeAnalyzerJob:
    def __init__(self):
        self.job = Job(name='股票交易量分析', print_interval=3)
        stock_list = DataProvider().get_stock_list()
        for stock in stock_list:
            self.job.add(stock)

    def get_stunt_point(self, code):
        result = {
            "code": code,
            'skip': False,
            "point": []
        }

        data = StockService.get_history_data(code)['data']
        data.reverse()
        data = data[:135]
        data.reverse()
        point_list = []
        for item in data:
            date = item[0]
            close_percent = item[8]
            fragment_data = get_history_fragment_trade_data(code[2:], date)
            if fragment_data is None:
                result['skip'] = True
                return result
            fragment_data = sorted(fragment_data, key=lambda fragment_item: fragment_item["amount"], reverse=True)
            point_list.append({
                "date": date,
                "data": fragment_data,
                "ceil": True if close_percent >= 9.9 else False
            })

        for idx, item in enumerate(point_list):
            first_item = item['data'][0]
            data_count = 5
            if idx < data_count:
                continue
            total = 0
            point_item_list = point_list[idx - data_count:idx]
            if len(point_item_list) != data_count:
                raise Exception('数据不匹配')
            for point_item in point_item_list:
                total += point_item['data'][0]['amount']
            average = total / data_count
            ratio = round(first_item['amount'] / average, 1)
            if ratio > 5 and not item['ceil'] and not point_list[idx - 1]['ceil']:
                result['point'].append({
                    "date": item['date'],
                    'time': first_item['time'],
                    "amount": first_item['amount'],
                    "type": first_item['type'],
                    "ratio": ratio
                })
        return result

    async def asynchronize_analyze_stock_volume(self, task_id, stock):
        code = stock['code']
        if stunt_document.find_one({"code": code}) is None:
            result = self.get_stunt_point(code)
            result['name'] = stock['name']
            stunt_document.save(result)
        self.job.success(task_id)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        loop = asyncio.get_event_loop()
        for task in self.job.task_list:
            stock = task['raw']
            task_id = task["id"]
            loop.run_until_complete(self.asynchronize_analyze_stock_volume(task_id, stock))


if __name__ == '__main__':
    StockVolumeAnalyzerJob().run()