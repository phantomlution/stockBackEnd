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

    def update_item(self, item, config):
        document = client.stock[config['document']]
        if document.find_one({"date": item['date'], "symbol": config['symbol']}) is None:
            item['symbol'] = config['symbol']
            item['type'] = config['type']
            document.save(item)

    def sync_item(self, config):
        _type = config['type']
        if _type in ['index', 'concept']:
            item_list = EastMoneyService.get_index_or_concept_one_minute_tick_data(config['symbol'], days=5)
            for item in item_list:
                self.update_item(item, config)
        elif _type in ['capital']:
            item = EastMoneyService.get_latest_hot_money_data(config['symbol'])
            self.update_item(item, config)

    def start(self):
        # 重建板块索引
        DataService.update_concept_block_index()
        for task in self.job.task_list:
            config = task['raw']
            task_id = task['id']
            try:
                self.sync_item(config)
                self.job.success(task['id'])
            except Exception as e:
                self.job.fail(task_id, e)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)


if __name__ == '__main__':
    # response = EastMoneyService.get_latest_concept_block_data('BK0940')
    # print(response)
    DataSyncJob().run()



