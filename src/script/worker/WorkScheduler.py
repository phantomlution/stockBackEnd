from src.script.worker.DataMonitorWorker import DataMonitorWorker
from src.script.worker.NewsScratchWorker import NewsScratchWorker
from functools import wraps
from src.service.LogService import LogService
import time
import threading
import schedule
import signal
import sys

news_scratch_worker = NewsScratchWorker()
data_monitor_worker = DataMonitorWorker()


def schedule_monitor(func):
    @wraps(func)
    def func_log(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(e)
            title = 'schedule_' + func.__name__
            LogService.error(title, e)

    return func_log


@schedule_monitor
def update_news():
    news_scratch_worker.get_central_bank_communication_news()
    news_scratch_worker.get_foreign_affair_news()
    news_scratch_worker.get_prc_board_meeting_news()
    news_scratch_worker.get_prc_collective_learning_news()
    news_scratch_worker.get_commerce_department_news_press_news()
    news_scratch_worker.get_cnbc_news()
    news_scratch_worker.get_sina_financial_news()


@schedule_monitor
def update_notification():
    data_monitor_worker.update_american_securities_yield()
    data_monitor_worker.update_central_bank_open_market_operation()
    data_monitor_worker.update_lpr_biding_change()
    data_monitor_worker.update_market_suspend_notice()


# 慢速更新
@schedule_monitor
def low_priority_update():
    data_monitor_worker.update_cnn_fear_greed_index()


@schedule_monitor
def user_update_track():
    pass


def run_continuously(interval=1):

    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()

    def signal_handler(signal, frame):
        cease_continuous_run.set()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    print('schedule thread started')
    return cease_continuous_run


# 提供给外部引用
def start_schedule():
    schedule.every(5).to(10).minutes.do(update_news)
    schedule.every(5).to(10).minutes.do(update_notification)
    schedule.every(5).to(10).minutes.do(user_update_track)
    schedule.every(45).to(60).minutes.do(low_priority_update)

    run_continuously(1 * 60)


if __name__ == '__main__':
    start_schedule()