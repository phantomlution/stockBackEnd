'''
    获取所有公告（个股公告第一页数据）
'''
from src.script.job.Job import Job
import json
from src.service.StockService import StockService
from src.service.HtmlService import get_response
import time
from src.utils.date import time_format, get_split_range
import datetime

client = StockService.getMongoInstance()
notice_document = client.stock.notice
sync_document = client.stock.sync


class StockNoticeJob:
    def __init__(self):
        self.sync_table_key = 'stock_notice_data'
        self.sync_duration = 1
        self.job = Job(name='股票公告')

    def load_stock_notice(self, date, page_no=1, page_size=50):
        url = "http://data.eastmoney.com/notices/getdata.ashx"
        params = {
            "StockCode": "",
            "FirstNodeType": 0,
            "CodeType": 1,
            "PageIndex": page_no,
            "PageSize": page_size,
            "jsObj": "NOkxwCpC",
            "SecNodeType": 0,
            "Time": date,
            "rt": 52356927
        }
        content = get_response(url, params=params, encoding='gbk')
        content_json_str = str.strip(content[content.find('=') + 1:-1])
        content_json = json.loads(content_json_str)
        return content_json

    def load_full_page_notice(self, date):
        result = []
        first_page = self.load_stock_notice(date)
        total_page = first_page['pages']
        for page in range(total_page):
            current_page = self.load_stock_notice(date, page + 1)
            for item in current_page['data']:
                model = StockService.parse_stock_notice_item(item)
                if model is None:
                    continue

                result.append(model)

        return result

    def synchronize_load_stock_notice(self, task_id, split_range):
        if split_range['start'] != split_range['end']:
            raise Exception('最多只允许一天的数据')
        time.sleep(0.3)

        date = split_range['start']
        item_list = self.load_full_page_notice(date)
        for item in item_list:
            notice_document.update({ "notice_id": item['notice_id'] }, item, True)
        model = {
            "key": self.sync_table_key,
            "last_update": date
        }
        sync_document.update({ "key": self.sync_table_key }, model, True)
        self.job.success(task_id)

    def run(self, end_func=None):
        self.init_task()
        self.job.start(self.start, end_func)

    def init_task(self):
        sync_model = sync_document.find_one({"key": self.sync_table_key})
        if sync_model is None:
            last_update = '2019-08-01'
        else:
            last_update = sync_model['last_update']

        # 开始同步数据
        current = datetime.datetime.now().strftime(time_format)
        split_range_list = get_split_range(last_update, current, self.sync_duration)
        for split_range in split_range_list:
            self.job.add(split_range)

    def start(self):
        for task in self.job.task_list:
            task_id = task["id"]
            split_range = task['raw']
            self.synchronize_load_stock_notice(task_id, split_range)


if __name__ == '__main__':
    StockNoticeJob().run()