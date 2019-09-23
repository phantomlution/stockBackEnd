'''
    提取部分已知的理财产品信息
    目前只实现了农行
'''

import json
import math
import datetime
from src.script.job.Job import Job
import asyncio
import time
from src.utils.sessions import FuturesSession
from src.service.StockService import StockService
client = StockService.getMongoInstance()
temp_document = client.stock.temp
session = FuturesSession(max_workers=1)


# 农行理财数据
class AgriculturalBankOfChina():

    def __init__(self):
        self.job = Job(name='中国农业银行理财产品')
        self.result = []


    def get_financial_product_page(self, page_number, page_size=15):
        time.sleep(0.5)
        url = 'http://ewealth.abchina.com/app/data/api/DataService/BoeProductOwnV2'
        params = {
            "i": page_number,
            "s": page_size,
            "o": 0,
            'w': '%7C%7C%7C%7C%7C%7C%7C1%7C%7C0%7C%7C0'
        }

        content = json.loads(session.get(url, params=params).result().content.decode())

        data = content['Data']
        page_model = {
            'page_number': page_number,
            'page_size': page_size,
            "total": data['Table1'][0]['total'],
            "list": data['Table']
        }
        return page_model

    async def get_financial_product_list(self, task_id, page_number):
        try:
            # 提取记录
            item_list = []
            page_result = self.get_financial_product_page(page_number + 1)
            for item in page_result['list']:
                item_list.append(item)

            for item in item_list:
                # 转换模型
                century = item['szComDat'][:2]
                if century != '20':
                    raise Exception('都22世纪了啊')

                last_sale_date = century + item['ProdSaleDate'].split('-')[-1]
                if '天' not in item['ProdLimit']:
                    raise Exception('日期单位异常')

                duration_in_days_str = item['ProdLimit'].split('天')[0]
                if str.isdigit(duration_in_days_str) is False:
                    print('弃用：{}'.format(duration_in_days_str))
                    continue

                duration_in_days = int(duration_in_days_str)
                start = datetime.datetime.strptime(last_sale_date, '%Y.%m.%d')
                end = start + datetime.timedelta(days=duration_in_days + 1)

                self.result.append({
                    "code": item['ProductNo'],
                    "name": item['ProdName'],
                    "class": item['ProdClass'],
                    "publisher": str.strip(item['issuingOffice']),
                    "area": item['ProdArea'],
                    "last_sale_date": datetime.datetime.strftime(start, '%Y-%m-%d'),
                    "end_date": datetime.datetime.strftime(end, '%Y-%m-%d')
                })

            self.job.success(task_id)
        except Exception as e:
            self.job.fail(task_id, e)
            print(e)

    def start(self):
        loop = asyncio.get_event_loop()
        for task in self.job.task_list:
            task_id = task['id']
            page_number = task['raw']['page_number']
            loop.run_until_complete(self.get_financial_product_list(task_id, page_number))

    def end_func(self):
        model = {
            "key": 'abc_financial_product',
            "list": self.result
        }

        temp_document.update({ "key": model['key']}, model, True)

    def run(self):
        # 获取总记录数
        first_page = self.get_financial_product_page(1)
        page_count = math.ceil(first_page['total'] / first_page['page_size'])

        # 构造任务参数队列
        for page_number in range(page_count):
            self.job.add({
                "page_number": page_number + 1
            })
        self.job.start(self.start, self.end_func)

if __name__ == '__main__':
    AgriculturalBankOfChina().run()