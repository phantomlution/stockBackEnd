'''
     数据库部分表备份
'''
from src.script.job.Job import Job
from src.service.DataWorker import DataWorker
import os

db_name = 'stock'
cache_dir = '/Users/yixiaoxiao/mongo_backup/'
zip_file_uri = '/Users/yixiaoxiao/Documents/mongo_backup.zip'


class DatabaseBackUpJob:

    def __init__(self):
        self.job = Job(name="数据库备份")
        task_list = [ # 备份的数据库表
            'base',
            'custom_event',
            'custom_event_item',
            'notification',
            'stock_pool',
            'huitong',
            'chess',
            'surge_for_short',
            'movie_series',
            'movie_comment'
        ]

        task_list += self.get_other_table()

        for task in task_list:
            self.job.add(task)

    def get_other_table(self):
        other_table = []
        item_list = DataWorker.get_sync_item_list()
        for item in item_list:
            table_name = item['document']
            if table_name not in other_table:
                other_table.append(table_name)

        return other_table

    def start(self):
        for idx, task in enumerate(self.job.task_list):
            try:
                table_name = task['raw']
                os.system('mongoexport --quiet -h localhost -d ' + db_name + ' -c ' + table_name + '  -o ' + cache_dir + table_name + '.json')
                if idx == (len(self.job.task_list) - 1):
                    os.system('cd ' + cache_dir + ';zip -r -q ' + zip_file_uri + ' .')
                    os.system('rm -f ' + cache_dir + '*')
                self.job.success(task['id'])
            except Exception as e:
                self.job.fail(task['id'], e)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    # 数据恢复
    def restore(self):
        for idx, task in enumerate(self.job.task_list):
            try:
                table_name = task['raw']
                os.system('mongoimport -h localhost -d ' + db_name + ' -c ' + table_name + '  --file ' + cache_dir + table_name + '.json')
            except Exception as e:
                print(e)


if __name__ == '__main__':
    DatabaseBackUpJob().run()
    # DatabaseBackUpJob().restore()