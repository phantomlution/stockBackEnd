'''
    获取股票交易数据
'''
from src.script.job.Job import Job
from src.utils.sessions import FuturesSession
from src.utils import date
import json
from src.service.StockService import StockService
from src.assets.DataProvider import DataProvider
import asyncio

client = StockService.getMongoInstance()
history_document = client.stock.history
session = FuturesSession(max_workers=1)


class StockTradeDataJob:
    def __init__(self):
        stock_list = DataProvider().get_stock_list()
        self.job = Job(name='股票交易数据')
        for stock in stock_list:
            self.job.add(stock)

    def load_stock_data(self, code):
        url = "http://pdfm.eastmoney.com/EM_UBG_PDTI_Fast/api/js"
        current = date.getCurrentTimestamp()
        params = {
            "rtntype": 6,
            # token: 4f1862fc3b5e77c150a2b985b12db0fd
            "cb": 'jQuery18308087247480464783_' + str(current),
            "id": code[2:] + ('2' if code[:2] == 'SZ' else '1'),
            "type": "k",
            "authorityType": 'fa', # 前复权
            "_": current
        }
        content = session.get(url, params=params).result().content.decode()
        content_json = str.strip(str(content)[len(params['cb']) + 1:-1])

        if content_json == '{stats:false}':
            raise Exception('数据异常')
        return json.loads(content_json)

    def update_stock_data(self, code):
        code = str.upper(code)
        item = self.load_stock_data(code)
        if len(item['data']) > 0:
            item['code'] = code
            item['column'] = [
                'date',
                'open',
                'close',
                'max',
                'min',
                'volume',  # 手数
                'amount',
                'amplitude'
            ]

            # 计算要数据转换的列
            need_parse_float_list = []
            for idx, field in enumerate(item['column']):
                if field not in ['date', 'amplitude']:
                    need_parse_float_list.append(idx)

            # 读取最新总流通股
            last_volume = item['flow'][-1]['ltg']

            # 数据量太大,只保留一部分
            data_list = []
            for data_index, data in enumerate(item['data'][-420:]):
                raw_data_arr = data.split(',')
                if len(raw_data_arr) != len(item['column']):
                    raise Exception('字段列数不匹配')
                data_arr = []
                # 进行数据类型转换
                for column_index, column in enumerate(raw_data_arr):
                    if column_index in need_parse_float_list:
                        data_arr.append(float(column))
                    else:
                        data_arr.append(column)

                # 计算涨跌幅
                close_field_index = item['column'].index('close')
                if data_index == 0:
                    percent = '-'
                else:
                    yesterday_close_value = data_list[data_index - 1][close_field_index]
                    today_close_value = data_arr[close_field_index]
                    percent = round((today_close_value - yesterday_close_value) * 100 / yesterday_close_value, 2)
                data_arr.append(percent)

                # 计算换手率，忽略历史流通股的影响，全部按照最新流通股计算，只关心成交量
                volume_index = item['column'].index('volume')
                # 手数转化成股票数量
                turnover_rate = round(data_arr[volume_index] * 100 * 100 / last_volume, 2)
                data_arr.append(turnover_rate)

                data_list.append(data_arr)

            item['column'].append('percent')
            item['column'].append('turnoverRate')
            item['data'] = data_list
            history_document.update({"code": item.get('code')}, item, True)
        else:
            raise Exception('找不到[{code}]的数据'.format(code=code))

    async def asynchronize_load_stock_data(self, task_id, code):
        # time.sleep(0.3)
        try:
            self.update_stock_data(code)
            self.job.success(task_id)
        except Exception as e:
            self.job.fail(task_id, e)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        history_document.drop()
        loop = asyncio.get_event_loop()
        for task in self.job.task_list:
            stock = task['raw']
            task_id = task["id"]
            code = stock.get('code')
            loop.run_until_complete(self.asynchronize_load_stock_data(task_id, code))


if __name__ == '__main__':
    StockTradeDataJob().run()
    # stock_code = 'SH000001'
    # print(StockTradeDataJob().update_stock_data(stock_code))