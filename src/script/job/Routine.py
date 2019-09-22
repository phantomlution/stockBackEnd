'''
    每日的任务调度
'''
from src.script.job.MarketCapitalDataJob import MarketCapitalDataJob
from src.script.job.StockBaseDataJob import StockBaseDataJob
from src.script.job.StockNoticeJob import StockNoticeJob
from src.script.job.StockThemeDataJob import StockThemeDataJob
from src.script.job.StockTradeDataJob import StockTradeDataJob
import schedule
import time


if __name__ == '__main__':
    # 进行中的任务
    running_task = []

    pending_task = [
        # 'StockBaseDataJob', # 数据库初始化时需要调用
        'StockTradeDataJob',
        'MarketCapitalDataJob',
        'StockThemeDataJob',
        'StockNoticeJob'
    ]

    # 最终采取pop
    pending_task.reverse()

    current_module = locals()

    def end_func():
        running_task.pop()

    def execute_next_task():
        next_task = pending_task.pop()
        if next_task is not None:
            running_task.append(next_task)
            current_job = current_module[next_task]()
            current_job.run(end_func=end_func)

    def check_task():
        if len(running_task) == 0:
            if len(pending_task) == 0:
                print('\nall job done')
                exit(0)
            else:
                execute_next_task()

    schedule.every(5).seconds.do(check_task)

    while True:
        schedule.run_pending()
        time.sleep(1)