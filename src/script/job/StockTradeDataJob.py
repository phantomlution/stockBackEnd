'''
    同步交易日数据
'''
from src.script.job.Job import Job
from src.assets.DataProvider import DataProvider
import asyncio
import time
import datetime
from src.utils.sessions import FuturesSession
from src.script.auth.Auth import Auth
import json
import numpy as np
from src.service.StockService import StockService

client = StockService.getMongoInstance()
history_document = client.stock.history
session = FuturesSession(max_workers=1)


class StockTradeDataJob:
    def __init__(self):
        self.cookies = {}
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://xueqiu.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
        }
        stock_list = DataProvider().get_stock_list()
        self.job = Job(name='股票交易数据')
        for stock in stock_list:
            self.job.add(stock)

    # 校验返回数据的时间序列是否正确
    def check_time_sequence(self, item_list, timestamp_position):
        for index, item in enumerate(item_list):
            if index > 0 and index < len(item_list):
                current = item_list[index]
                former = item_list[index - 1]
                if current[timestamp_position] < former[timestamp_position]:
                    return False
        return True

    def extract_column(self, item_list, index):
        result = []
        for item in item_list:
            result.append(item[index])
        return result

    def extract_stock_data(self, raw):
        data = raw['data']
        if 'symbol' not in data:
            raise Exception('数据不存在')
        code = data['symbol']
        column = data['column']
        itemList = data['item']
        totalLength = len(itemList)
        if totalLength == 0:
            raise Exception('无数据')

        if self.check_time_sequence(itemList, column.index('timestamp')) is not True:
            raise Exception('序列错误')

        closeList = self.extract_column(itemList, column.index('close'))
        jidazhi = []
        for index, stock in enumerate(closeList):
            if index > 0 and index < len(closeList) - 1:
                former = closeList[index - 1]
                current = closeList[index]
                later = closeList[index + 1]
                if current >= former and current >= later:
                    jidazhi.append(current)

        jixiaozhi = []
        for index, stock in enumerate(closeList):
            if index > 0 and index < len(closeList) - 1:
                former = closeList[index - 1]
                current = closeList[index]
                later = closeList[index + 1]
                if current <= former and current <= later:
                    jixiaozhi.append(current)

        lastItem = itemList[-1]
        lastEndPrice = lastItem[column.index('close')]
        maxAverage = np.mean(jidazhi)
        minAverage = np.mean(jixiaozhi)
        totalAverage = np.mean([maxAverage, minAverage])
        diffPercent = (lastEndPrice - totalAverage) / totalAverage * 100

        return {
            "code": code,
            "last": lastEndPrice,
            "maxAverage": maxAverage,
            "minAverage": minAverage,
            "diffPercent": diffPercent,
            "avg": totalAverage,
            "count": totalLength,
            "column": column,
            "data": itemList,
            "updateDate": int(datetime.datetime.now().timestamp() * 1000 // 1)
        }

    def get_stock_history_data(self, code, days):
        session.head('https://xueqiu.com/S/' + code)

        url = 'https://stock.xueqiu.com/v5/stock/chart/kline.json'
        timestamp = str(int(datetime.datetime.now().timestamp() * 1000 // 1))
        indicator = 'kline,ma,macd,kdj,boll,rsi,wr,bias,cci,psy,pe,pb,ps,pcf,market_capital,agt,ggt,balance'
        params = {
            'symbol': code,
            'begin': timestamp,
            'period': 'day',
            'type': 'before',
            'count': '-' + str(days),
            'indicator': indicator
        }
        return session.get(url, params=params, headers=self.headers, cookies=self.cookies)

    def get_stock(self, code, count):
        result = self.get_stock_history_data(code, count).result()
        string_response = result.content.decode()

        return self.extract_stock_data(json.loads(string_response))

    async def update_stock_document(self, task_id, stock):
        time.sleep(0.3)
        try:
            item = self.get_stock(stock.get('code'), 420)
            history_document.update({"code": item.get("code")}, item, True)
            self.job.success(task_id)
        except Exception as e:
            self.job.fail(task_id, e)
            print(e)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        history_document.drop()
        loop = asyncio.get_event_loop()
        self.cookies = Auth.get_snow_ball_auth()
        task_list = self.job.task_list
        for task in task_list:
            stock = task['raw']
            task_id = task['id']
            loop.run_until_complete(self.update_stock_document(task_id, stock))
