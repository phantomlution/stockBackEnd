'''
    获取所有公告（个股公告第一页数据）
'''
from src.script.job.Job import Job
from src.utils.sessions import FuturesSession
import json
from src.service.StockService import StockService
from src.assets.DataProvider import DataProvider
import time
import asyncio

client = StockService.getMongoInstance()
notice_document = client.stock.notice
session = FuturesSession(max_workers=1)


class StockNoticeJob:
    def __init__(self):
        stock_list = DataProvider().get_stock_list()
        self.job = Job(name='股票公告')
        for stock in stock_list:
            self.job.add(stock)

    def load_stock_notice(self, code):
        url = "http://data.eastmoney.com/notices/getdata.ashx"
        params = {
            "StockCode": code,
            "CodeType": 1,
            "PageIndex": 1,
            "PageSize": 50,
            "jsObj": "dHBlUEvg",
            "SecNodeType": 0,
            "FirstNodeType": 0
        }
        content = session.get(url, params=params).result().content.decode('gbk')
        content_json = str.strip(content[content.find('=') + 1:-1])
        return content_json

    async def asynchronize_load_stock_notice(self, task_id, code):
        time.sleep(0.8)
        try:
            item = self.load_stock_notice(code)
            if item is not None:
                item = json.loads(item)
                if len(item['data']) > 0:
                    item['code'] = code
                    notice_document.update({"code": item.get('code')}, item, True)
                self.job.success(task_id)
            else:
                raise Exception('找不到[{code}]的公告'.format(code=code))
        except Exception as e:
            self.job.fail(task_id, e)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        notice_document.drop()
        loop = asyncio.get_event_loop()
        for task in self.job.task_list:
            stock = task['raw']
            task_id = task["id"]
            code = stock.get('code')[2:]
            loop.run_until_complete(self.asynchronize_load_stock_notice(task_id, code))