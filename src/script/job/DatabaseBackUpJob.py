'''
     数据库部分表备份
'''
from src.script.job.Job import Job
from src.service.DataService import DataService
import os


class DatabaseBackUpJob:

    def __init__(self):
        self.job = Job(name="数据库备份")
        task_list = [ # 备份的数据库表
            'custom_event',
            'custom_event_item',
            'notification',
            'stock_pool',
            'huitong',
            'chess',
        ]

        task_list += self.get_other_table()

        for task in task_list:
            self.job.add(task)

    def get_other_table(self):
        other_table = []
        item_list = DataService.get_sync_item_list()
        for item in item_list:
            table_name = item['document']
            if table_name not in other_table:
                other_table.append(table_name)

        return other_table

    def start(self):
        db_name = 'stock'
        back_up_path = '/Users/yixiaoxiao/Documents/db_backup/'
        for task in self.job.task_list:
            try:
                table_name = task['raw']
                os.system('mongoexport --quiet -h localhost -d ' + db_name + ' -c ' + table_name + '  -o ' + back_up_path + table_name + '.json')
                self.job.success(task['id'])
            except Exception as e:
                self.job.fail(task['id'], e)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)


if __name__ == '__main__':
    DatabaseBackUpJob().run()