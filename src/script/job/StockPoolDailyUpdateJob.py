'''
    更新股票池中的数据（每日同步部分数据）
    目前有：
        1. 预发布公告
'''
from src.script.job.Job import Job
from src.service.StockService import StockService
import asyncio

client = StockService.getMongoInstance()


class StockPoolDailyUpdateJob:
    def __init__(self):
        stock_pool_list = client.stock.stock_pool.find()
        stock_list = stock_pool_list
        self.job = Job(name='已选股票每日更新')
        for stock in stock_list:
            self.job.add(stock)

    async def asynchronize_update_stock_daily(self, task_id, code):
        # 目前只更新预披露信息
        try:
            StockService.update_stock_pre_release(code)
            self.job.success(task_id)
        except Exception as e:
            self.job.fail(task_id, e)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        loop = asyncio.get_event_loop()
        for task in self.job.task_list:
            stock = task['raw']
            task_id = task["id"]
            code = stock.get('code')
            loop.run_until_complete(self.asynchronize_update_stock_daily(task_id, code))


if __name__ == '__main__':
    stock_code = 'SH600392'
    StockService.update_stock_pre_release(stock_code)
