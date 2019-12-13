'''
    用于整个任务的调度

    必须调用 run(start_func, [end_func]) 启动任务
'''
import uuid
import datetime
from threading import Timer
import math


class Job:
    def __init__(self, name, print_interval=60):
        self.name = name
        self.id = str(uuid.uuid4())
        self.task_list = []
        self.success_list = []
        self.fail_list = []
        self.start_time = None
        self.end_time = None
        self.execute_duration = 0
        self.done_func = None
        self.timer = None
        self.progress_timer_interval = print_interval  # 打印进度间隔

    # 生成任务列表
    def add(self, data):
        self.task_list.append({
            "id": self.id + "_" + str(len(self.task_list)),
            "raw": data
        })

    # 任务执行成功
    def success(self, task_id):
        self.success_list.append({
            "id": task_id
        })
        self.check_progress()

    # 任务执行失败
    def fail(self, task_id, error):
        self.fail_list.append({
            "id": task_id,
            "error": error
        })
        # 打印失败信息
        for task in self.task_list:
            if task["id"] == task_id:
                print('\n--- [{}] failed ---\n'.format(task_id))
                print('[{}]{}'.format(self.name, task['raw']))
                print(error)
                print('\n--- [{}] failed ---\n'.format(task_id))
                break
        self.check_progress()

    def check_progress(self):
        progress = self.get_progress()
        if progress['done']:
            self.end()
            if self.done_func is not None:
                self.done_func()

    # 必须手动触发任务
    def start(self, start_func, done_func=None):
        self.start_time = datetime.datetime.now()
        self.done_func = done_func
        print('')
        self.start_progress_timer()
        start_func()

    def end(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        self.end_time = datetime.datetime.now()
        self.execute_duration = (self.end_time - self.start_time).seconds
        progress = self.get_progress()
        print(progress)
        if progress["fail"] > 0:
            print('有{}条任务失败'.format(progress['fail']))

    # 打印实时进度
    def start_progress_timer(self):
        progress = self.get_progress()
        if progress['done']:
            return
        print(progress)
        self.timer = Timer(self.progress_timer_interval, self.start_progress_timer)
        self.timer.start()

    # 获取进度
    def get_progress(self):
        total_count = len(self.task_list)
        success_count = len(self.success_list)
        fail_count = len(self.fail_list)
        finish_count = success_count + fail_count
        is_done = finish_count == total_count
        cost_in_seconds = (datetime.datetime.now() - self.start_time).seconds if is_done is False else self.execute_duration

        return {
            "done": is_done,
            "name": self.name,
            "total": total_count,
            "finish": finish_count,
            "success": success_count,
            "fail": fail_count,
            "cost": '{}m{}s'.format(math.floor(cost_in_seconds / 60), cost_in_seconds % 60)
        }