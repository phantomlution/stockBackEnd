'''
     同步大盘资金数据
'''
from src.script.job.Job import Job
from src.utils.sessions import FuturesSession
import json
from src.service.stockService import StockService
from src.utils import date
import time

client = StockService.getMongoInstance()
capital_flow_document = client.stock.capitalFlow
hot_money_document = client.stock.hotMoney
session = FuturesSession(max_workers=1)


class MarketCapitalDataJob:

    def __init__(self):
        self.job = Job(name="大盘资金数据")
        task_list = [
            'synchronize_capital_flow',
            'synchronize_hot_money'
        ]
        for task in task_list:
            self.job.add(task)

    def get_real_time_capital_flow(self):
        url = 'http://ff.eastmoney.com/EM_CapitalFlowInterface/api/js'
        params = {
            "id": "ls",
            "type": "ff",
            "check": "MLBMS",
            "cb": "var aff_data =",
            "js": "{(x)}",
            "rtntype": 3,
            "date": "2019-09-11",
            "acces_token": "1942f5da9b46b069953c873404aad4b5",
            "_": date.getCurrentTimestamp()
        }

        content = session.get(url, params=params).result().content
        content = str(content)
        content_json = str.strip(content[content.find('=') + 1:-1])
        return json.loads(content_json)

    def synchronize_capital_flow(self):
        data = self.get_real_time_capital_flow()
        if 'ya' not in data:
            raise Exception('[大盘资金]数据异常')
        # [0] 主力净流入
        # [1] 超大单净流入
        # [2] 大单净流入
        # [3] 中单净流入
        # [4] 小单净流入
        ya = data['ya']
        last_ya_item = ya[-1]
        if last_ya_item == ',,,,':
            raise Exception('[大盘资金]数据不完整，请于15点后同步')

        model = {
            "date": date.format_timestamp(date.getCurrentTimestamp()),
            "data": data
        }

        capital_flow_document.update({"date": model["date"]}, model, True)


    def get_hot_money_data(self):
        url = 'http://push2.eastmoney.com/api/qt/kamt.rtmin/get'
        current = date.getCurrentTimestamp()
        params = {
            "fields1": "f1,f2,f3,f4",
            "fields2": "f51,f52,f53,f54,f55,f56",
            "cb": "jQuery18304445605268991899_" + str(current),
            "_": current
        }

        headers = {
            "Referer": "http://data.eastmoney.com/hsgt/index.html",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
        }

        content = session.get(url, params=params, headers=headers).result().content
        content = str(content)[len(params['cb']) + 3:-3]
        return json.loads(content)

    def synchronize_hot_money(self):
        raw = self.get_hot_money_data()
        if 'data' not in raw:
            raise Exception('[北向资金]数据异常')
        raw_data = raw['data']
        response_date = raw_data['n2sDate']
        current_date = time.strftime('%m-%d')
        if response_date != current_date:
            raise Exception('[北向资金]没有当天的数据')

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

        raw_data['date'] = time.strftime('%Y-%m-%d')
        hot_money_document.update({"date": raw_data["date"]}, raw_data, True)

    def start(self):
        for task in self.job.task_list:
            try:
                func = getattr(self, task['raw'])
                func()
                self.job.success(task['id'])
            except Exception as e:
                self.job.fail(task["id"], e)
                print(e)


    def end(self):
        print(self.job.get_progress())
        pass


    def run(self):
        self.job.start(self.start, self.end)