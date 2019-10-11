'''
    同步债券重大事项
'''
import json
from src.utils.date import time_format, get_split_range
import time
from src.service.StockService import StockService
import datetime
from src.utils.sessions import FuturesSession
from src.script.job.Job import  Job
session = FuturesSession(max_workers=1)

client = StockService.getMongoInstance()
sync_document = client.stock.sync
bond_risk_document = client.stock.bond_risk


class BondRiskDataJob:

    def __init__(self):
        #  同步数据间隔的天数
        self.sync_duration = 2
        self.sync_table_key = 'bond_risk_data'
        self.job = Job(name='债券重大事项同步')

    def load_bond_risk(self, start, end, page_no=1, page_size=30):
        url = "http://www.chinamoney.com.cn/ags/ms/cm-u-notice-issue/majorMatters"
        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
        }
        params = {
            "eventCode": "",
            "drftClAngl": "1001",
            "bondNameOrCode": '',
            "pageNo": page_no,
            "pageSize": page_size,
            "startDate": start,
            "endDate": end,
            "limit": 1,
            "timeln": 1
        }

        return json.loads(session.post(url, data=params, headers=headers).result().content)

    # 获取完整的数据，由分页数据拼接而成
    def get_total_data(self, start, end):
        return_result = []
        init_data = self.load_bond_risk(start, end)
        page_count = init_data['data']['pageTotalSize']
        for page_number in range(1, page_count + 1):
            page = self.load_bond_risk( start, end, page_number)
            for record in page['records']:
                return_result.append(record)

        return return_result

    def sync_data(self, split_range):
        # 按照指定区间同步数据
        total_data = self.get_total_data(split_range['start'], split_range['end'])
        for item in total_data:
            bond_risk_document.update({ "contentId": item["contentId"]}, item, True)

        # 更新进度表
        sync_document.update({ "key": self.sync_table_key}, {
            "key": self.sync_table_key,
            "last_update": split_range['end']
        }, True)
        time.sleep(0.3)

    def run(self, end_func=None):
        self.init_task()
        self.job.start(self.start, end_func)

    def init_task(self):
        sync_model = sync_document.find_one({"key": self.sync_table_key})
        if sync_model is None:
            last_update = '2019-05-01'
        else:
            last_update = sync_model['last_update']

        # 开始同步数据
        current = datetime.datetime.now().strftime(time_format)
        split_range_list = get_split_range(last_update, current, self.sync_duration)
        for split_range in split_range_list:
            self.job.add(split_range)

    def start(self):
        for task in self.job.task_list:
            task_id = task['id']
            split_range = task['raw']
            try:
                self.sync_data(split_range)
                self.job.success(task_id)
            except Exception as e:
                self.job.fail(task_id, e)
