'''
    关联股票限售信息
'''
from src.assets.DataProvider import DataProvider
from src.script.job.Job import Job
from src.service.StockService import StockService
import time
import random

client = StockService.getMongoInstance()
base_document = client.stock.base


class StockRestrictSellUpdateJob:

    def __init__(self):
        stock_list = DataProvider().get_stock_list()
        self.cookie = None
        self.job = Job(name='关联股票限售信息')
        for stock in stock_list:
            self.job.add(stock)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        success_count = 1
        for task in self.job.task_list:
            task_id = task['id']
            stock = task['raw']
            code = stock['code']
            stock_base = base_document.find_one({"symbol": code})
            if 'restrict_sell_list' not in stock_base:
                time.sleep(1 + random.random() * 1)
                restrict_sell_list = StockService.get_restricted_sell_stock(code)
                base_document.update({"symbol": code}, {'$set': {'restrict_sell_list': restrict_sell_list}}, True)
                success_count += 1
                if success_count % 30 == 0:
                    time.sleep(10)
            self.job.success(task_id)


if __name__ == '__main__':
    def start_mission():
        try:
            StockRestrictSellUpdateJob().run()
        except:
            time.sleep(60)
            start_mission()

    start_mission()