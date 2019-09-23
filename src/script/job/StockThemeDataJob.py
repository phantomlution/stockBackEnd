'''
    获取所有个股所在的主题概念
'''
from src.script.job.Job import Job
from src.utils.sessions import FuturesSession
import json
from src.service.StockService import StockService
from src.assets.DataProvider import DataProvider
import time
import asyncio

client = StockService.getMongoInstance()
theme_document = client.stock.theme
session = FuturesSession(max_workers=1)


class StockThemeDataJob:
    def __init__(self):
        stock_list = DataProvider().get_stock_list()
        self.job = Job(name='股票主题')
        for stock in stock_list:
            self.job.add(stock)

    def load_stock_theme(self, code):
        url = "http://f10.eastmoney.com/CoreConception/CoreConceptionAjax"
        params = {
            "code": code
        }
        content = session.get(url, params=params).result().content
        response = json.loads(content)
        if 'hxtc' in response:
            if len(response['hxtc']) > 0:
                return response['hxtc'][0]['ydnr'].split(' ')

        return None

    async def asynchronize_load_stock_theme(self, task_id, code):
        time.sleep(0.3)
        try:
            theme = self.load_stock_theme(code)
            if theme is not None:
                model = {
                    "code": code,
                    "theme": theme
                }
                theme_document.update({"code": model.get('code')}, model, True)
                self.job.success(task_id)
            else:
                raise Exception('找不到[{code}]的主题'.format(code=code))
        except Exception as e:
            self.job.fail(task_id, e)
            print(e)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        theme_document.drop()
        loop = asyncio.get_event_loop()
        for task in self.job.task_list:
            stock = task['raw']
            task_id = task["id"]
            code = stock.get('code')
            loop.run_until_complete(self.asynchronize_load_stock_theme(task_id, code))