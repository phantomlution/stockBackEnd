'''
    用于整个任务的调度

    必须调用 run(start_func, [end_func]) 启动任务
'''
import uuid
import datetime


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
        start_func()

    def end(self):
        self.end_time = datetime.datetime.now()
        self.execute_duration = (self.end_time - self.start_time).seconds

    # 获取进度
    def get_progress(self):
        total_count = len(self.task_list)
        success_count = len(self.success_list)
        fail_count = len(self.fail_list)
        finish_count = success_count + fail_count

        return {
            "done": finish_count == total_count,
            "name": self.name,
            "total": total_count,
            "finish": finish_count,
            "success": success_count,
            "fail": fail_count,
            "cost_in_seconds": self.execute_duration
        }