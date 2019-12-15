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
        for data_item in data:
            date = data_item[0]
            close_percent = data_item[8]
            yesterday_close = round(data_item[2] / (1 + close_percent / 100), 2)
            fragment_data = get_history_fragment_trade_data(code[2:], date)
            if fragment_data is None:
                result['skip'] = True
                return result
            fragment_data = sorted(fragment_data, key=lambda fragment_item: fragment_item["amount"], reverse=True)
            point_list.append({
                "date": date,
                "data": fragment_data,
                'yesterday': yesterday_close,
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
                    "price": first_item['price'],
                    'yesterday': item['yesterday'],
                    "ratio": ratio
                })
        return result

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        for task in self.job.task_list:
            stock = task['raw']
            task_id = task["id"]
            code = stock['code']
            if stunt_document.find_one({"code": code}) is None:
                result = self.get_stunt_point(code)
                result['name'] = stock['name']
                stunt_document.save(result)
            self.job.success(task_id)


def temporary_patch():
    stock_list = DataProvider().get_stock_list()
    history_document = client.stock.history
    count = 0
    for stock in stock_list:
        count += 1
        print(count)
        code = stock['code']
        stunt_item = stunt_document.find_one({"code": code})
        if stunt_item is None:
            continue
        if 'patched' in stunt_item and stunt_item['patched']:
            continue
        if stunt_item is not None and len(stunt_item['point']) > 0:
            history_data = history_document.find_one({"code": code})['data']
            for point_item in stunt_item['point']:
                date = point_item['date']
                _time = point_item['time']
                result_list = list(filter(lambda item: item[0] == date, history_data))
                if len(result_list) != 1:
                    raise Exception('error')
                data_item = result_list[0]
                close_percent = data_item[8]
                yesterday_close = round(data_item[2] / (1 + close_percent / 100), 2)
                point_item['yesterday'] = yesterday_close
                fragment_data = get_history_fragment_trade_data(code[2:], date)
                fragment_data_filter = list(filter(lambda item: item['time'] == _time and item['amount'] == point_item['amount'], fragment_data))
                if len(fragment_data_filter) != 1:
                    raise Exception('error2')
                fragment_item = fragment_data_filter[0]
                point_item['price'] = fragment_item['price']
        stunt_item['patched'] = True
        stunt_document.update({"_id": stunt_item['_id']}, stunt_item)


if __name__ == '__main__':
    # StockVolumeAnalyzerJob().run()
    temporary_patch()
