'''
    数据同步服务
'''

from src.service.EastMoneyService import EastMoneyService
from src.service.DataService import DataService
from src.script.job.Job import Job
from src.service.StockService import StockService

client = StockService.getMongoInstance()

index_document = client.stock.sync_index
concept_document = client.stock.sync_concept


index_list = [
    {
        "name": '上证指数',
        "secid": '1.000001'
    }
]

# TODO
etf_list = []


class DataSyncJob:

    def __init__(self):
        self.job = Job('每日其他数据同步')

        # 添加指数
        for item in index_list:
            self.job.add({
                "type": 'index',
                "name": item['name'],
                "secid": item['secid']
            })

        # 添加概念数据
        for item in DataService.get_concept_block_item_list():
            self.job.add({
                "type": 'concept',
                "name": item['name'],
                "secid": '90.' + item['code']
            })

    def sync_index_data(self, config):
        item_list = EastMoneyService.get_index_or_concept_one_minute_tick_data(config['secid'], days=5)
        for item in item_list:
            if index_document.find_one({ "date": item['date'], "secid": config['secid'] }) is None:
                index_document.save(item)

    def sync_concept_data(self, config):
        item_list = EastMoneyService.get_index_or_concept_one_minute_tick_data(config['secid'], days=5)
        for item in item_list:
            if concept_document.find_one({ "date": item['date'], "secid": config['secid'] }) is None:
                concept_document.save(item)

    def start(self):
        for task in self.job.task_list:
            config = task['raw']
            task_id = task['id']
            try:
                if config['type'] == 'index':
                    self.sync_index_data(config)
                elif config['type'] == 'concept':
                    self.sync_concept_data(config)
                else:
                    raise Exception('类型错误')
                self.job.success(task['id'])
            except Exception as e:
                self.job.fail(task_id, e)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)


if __name__ == '__main__':
    # response = EastMoneyService.get_latest_concept_block_data('BK0940')
    # print(response)
    DataSyncJob().run()