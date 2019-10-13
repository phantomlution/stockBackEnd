'''
    获取所有个股基本信息
'''
from src.script.job.Job import Job
from src.utils.sessions import FuturesSession
import json
from src.service.StockService import StockService
from src.assets.DataProvider import DataProvider
from src.script.auth.Auth import Auth
import time
import asyncio

client = StockService.getMongoInstance()
base_document = client.stock.base
session = FuturesSession(max_workers=1)


class StockBaseDataJob:
    def __init__(self):
        self.cookies = {}
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://xueqiu.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
        }
        stock_list = DataProvider().get_stock_list()
        self.job = Job(name='股票基本信息')
        for stock in stock_list:
            self.job.add(stock)

    def load_stock_base(self, code):
        # 基本信息
        url = 'https://stock.xueqiu.com/v5/stock/quote.json?symbol=' + str(code)
        return json.loads(session.get(url, headers=self.headers, cookies=self.cookies).result().content.decode())

    def load_stock_company_introduction(self, code):
        url = 'https://stock.xueqiu.com/v5/stock/f10/cn/company.json?symbol=' + str(code)
        response = json.loads(session.get(url, headers=self.headers, cookies=self.cookies).result().content.decode())
        return response['data']['company']

    async def asynchronize_load_stock_base(self, task_id, code):
        old_item = base_document.find_one({"symbol": code })
        if old_item is not None and 'company' in old_item and old_item['company'] is not None:
            return self.job.success(task_id)

        time.sleep(0.5)
        try:
            item = self.load_stock_base(code).get('data').get('quote')
            if item is not None:
                item["company"] = self.load_stock_company_introduction(code)

                base_document.update({"symbol": item.get('symbol')}, item, True)
                self.job.success(task_id)
            else:
                raise Exception('找不到[{code}]的基本信息'.format(code=code))
        except Exception as e:
            self.job.fail(task_id, e)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        self.cookies = Auth.get_snow_ball_auth()
        loop = asyncio.get_event_loop()
        for task in self.job.task_list:
            stock = task['raw']
            task_id = task["id"]
            code = stock.get('code')
            loop.run_until_complete(self.asynchronize_load_stock_base(task_id, code))


if __name__ == '__main__':
    StockBaseDataJob().run()