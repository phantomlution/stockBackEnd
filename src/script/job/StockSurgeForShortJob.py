'''
    [跌]拉高出货点分析
'''
from src.script.job.Job import Job
from src.assets.DataProvider import DataProvider
from src.service.StockService import StockService
from src.service.AnalyzeService import AnalyzeService


class StockSurgeForShortJob:
    def __init__(self):
        stock_list = StockService.get_stock_pool()
        # stock_list = [
        #     {
        #         "code": "SZ002941",
        #         "name": 'xjjj'
        #     }
        # ]
        self.job = Job(name='[跌]拉高出货点分析')
        for stock in stock_list:
            if '指数' not in stock['name']:
                self.job.add(stock)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        for task in self.job.task_list:
            stock = task['raw']
            task_id = task["id"]
            code = stock.get('code')
            history_item_list = StockService.get_history_data(code)
            # 分析最近10个交易日的数据
            for item in history_item_list['data'][-200:]:
                _date = item[0]
                AnalyzeService.get_surge_for_short(code, _date)
            self.job.success(task_id)


if __name__ == '__main__':
    StockSurgeForShortJob().run()