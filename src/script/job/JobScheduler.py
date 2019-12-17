'''
    简化任务的调度
'''
import schedule
import time


class JobScheduler:

    def __init__(self, job_class_list, context_locals):
        self.running_task = []
        self.pending_task = job_class_list
        self.pending_task.reverse()
        self.current_module = context_locals
        self.statistic = {
            "fail": []
        }

    def start(self):
        def end_func():
            self.running_task.pop()

        def execute_next_task():
            next_task = self.pending_task.pop()
            if next_task is not None:
                self.running_task.append(next_task)
                current_job = self.current_module[next_task]()
                current_job.run(end_func=end_func)
                for fail_item in current_job.job.fail_list:
                    self.statistic['fail'].append(fail_item)

        def check_task():
            if len(self.running_task) == 0:
                if len(self.pending_task) == 0:
                    print('\nAll job done, 失败{fail}条'.format(fail=len(self.statistic['fail'])))
                    exit(0)
                else:
                    execute_next_task()

        check_task()
        schedule.every(5).seconds.do(check_task)

        while True:
            schedule.run_pending()
            time.sleep(1)