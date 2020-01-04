'''
    数据同步服务
'''

from src.service.EastMoneyService import EastMoneyService
from src.script.job.Job import Job
from src.service.StockService import StockService
from src.service.DataService import DataService

client = StockService.getMongoInstance()


class DataSyncJob:

    def __init__(self):
        self.job = Job('每日其他数据同步')

        for item in DataService.get_sync_item_list():
            self.job.add(item)

    def sync_index_or_concept(self, config):
        item_list = EastMoneyService.get_index_or_concept_one_minute_tick_data(config['secid'], days=5)
        document = client.stock[config['document']]
        for item in item_list:
            if document.find_one({ "date": item['date'], "secid": config['secid'] }) is None:
                document.save(item)

    def start(self):
        for task in self.job.task_list:
            config = task['raw']
            task_id = task['id']
            try:
                if config['type'] == 'index' or config['type'] == 'concept':
                    self.sync_index_or_concept(config)
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