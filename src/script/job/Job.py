'''
    用于整个任务的调度

    必须调用 run(start_func, [end_func]) 启动任务
'''
import uuid
import datetime
from threading import Timer


class Job:
    def __init__(self, name):
        self.name = name
        self.id = str(uuid.uuid4())
        self.task_list = []
        self.success_list = []
        self.fail_list = []
        self.start_time = None
        self.end_time = None
        self.execute_duration = 0
        self.done_func = None
        self.progress_timer_interval = 60  # 打印进度间隔

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
            ""
            "error": error
        })
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
        timer = Timer(self.progress_timer_interval, self.start_progress_timer)
        timer.start()

    # 获取进度
    def get_progress(self):
        total_count = len(self.task_list)
        success_count = len(self.success_list)
        fail_count = len(self.fail_list)
        finish_count = success_count + fail_count
        is_done = finish_count == total_count

        return {
            "done": is_done,
            "name": self.name,
            "total": total_count,
            "finish": finish_count,
            "success": success_count,
            "fail": fail_count,
            "cost_in_seconds": (datetime.datetime.now() - self.start_time).seconds if is_done is False else self.execute_duration
        }