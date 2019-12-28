'''
     数据库部分表备份
'''
from src.script.job.Job import Job
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
            'chess'
        ]
        for task in task_list:
            self.job.add(task)

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