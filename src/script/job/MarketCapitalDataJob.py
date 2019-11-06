'''
     同步大盘资金数据
'''
from src.script.job.Job import Job
from src.utils.sessions import FuturesSession
from src.service.StockService import StockService

client = StockService.getMongoInstance()
capital_flow_document = client.stock.capitalFlow
hot_money_document = client.stock.hotMoney
session = FuturesSession(max_workers=1)


class MarketCapitalDataJob:

    def __init__(self):
        self.job = Job(name="大盘资金数据")
        task_list = [
            'synchronize_hot_money'
        ]
        for task in task_list:
            self.job.add(task)

    def synchronize_hot_money(self):
        raw_data = StockService.get_hot_money_data()
        '''
            s2n: 北向资金
                0. 时间点
                1. 沪股通流入金额
                2. 沪股通余额
                3. 深股通流入金额
                4. 深股通余额

            n2s: 南向资金
                0. 时间点
                1. 港股通(沪)流入金额
                2. 港股通(沪)余额
                3. 港股通(深)流入金额
                4. 港股通(深)余额
        '''
        hot_money_document.update({"date": raw_data["date"]}, raw_data, True)

    def start(self):
        for task in self.job.task_list:
            func = getattr(self, task['raw'])
            func()
            self.job.success(task['id'])

    def run(self, end_func=None):
        self.job.start(self.start, end_func)


if __name__ == '__main__':
    MarketCapitalDataJob().run()