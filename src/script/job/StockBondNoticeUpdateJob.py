'''
    更新股票债券相关信息（每日同步全部数据）
    1. 债券发行信息
    2. 债券风险信息
'''
from src.script.job.Job import Job
from src.utils.sessions import FuturesSession
from src.service.StockService import StockService
from src.assets.DataProvider import DataProvider
import asyncio

client = StockService.getMongoInstance()
bond_notice_document = client.stock.bond_notice
base_document = client.stock.base
session = FuturesSession(max_workers=1)


class StockBondNoticeUpdateJob:
    def __init__(self):
        stock_list = DataProvider().get_stock_list()
        self.job = Job(name='股票-债券公告关联')
        for stock in stock_list:
            self.job.add(stock)

    async def asynchronize_update_stock_bond_notice(self, task_id, code):
        stock_base = client.stock.base.find_one({ "symbol": code })
        if stock_base is not None:
            # 关联目前已有的所有子公司债券信息
            company_name_list = [
                stock_base['company']['org_name_cn']
            ]
            if 'sub_company_list' in stock_base:
                for sub_company in stock_base['sub_company_list']:
                    if len(sub_company['company_name']) > 0:
                        company_name_list.append(sub_company['company_name'])

            # 获取债券发行信息
            bond_publish_list = list(client.stock.bond.find({"data.publish_company": {"$in": company_name_list }, "bond_type_name": {"$ne": "同业存单"}}, { "_id": 0 }))
            # 查询对应的债券风险信息
            bond_risk_list = list(client.stock.bond_risk.find({ "title": { "$in": company_name_list }}, { "_id": 0}))
            base_document.update({ 'symbol': code }, { '$set': {'bond_risk_list': bond_risk_list, "bond_publish_list": bond_publish_list } }, True)
        self.job.success(task_id)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        loop = asyncio.get_event_loop()
        for task in self.job.task_list:
            stock = task['raw']
            task_id = task["id"]
            code = stock.get('code')
            loop.run_until_complete(self.asynchronize_update_stock_bond_notice(task_id, code))


if __name__ == '__main__':
    StockBondNoticeUpdateJob().run()