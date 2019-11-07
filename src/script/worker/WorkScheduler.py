from src.script.worker.DataMonitorWorker import DataMonitorWorker
from src.script.worker.NewsScratchWorker import NewsScratchWorker
from functools import wraps
from src.service.NotificationService import NotificationService
from src.utils.date import get_current_datetime_str
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
            func_name = func.__name__
            NotificationService.add('schedule_failed', {
                "title": func_name + '执行失败',
                "raw": {
                    "id": func_name + get_current_datetime_str()
                }
            })

    return func_log


@schedule_monitor
def update_news():
    news_scratch_worker.get_central_bank_communication_news()
    news_scratch_worker.get_foreign_affair_news()
    news_scratch_worker.get_prc_board_meeting_news()
    news_scratch_worker.get_prc_collective_learning_news()
    news_scratch_worker.get_commerce_department_news_press_news()


@schedule_monitor
def update_notification():
    data_monitor_worker.update_cnn_fear_greed_index()
    data_monitor_worker.update_american_securities_yield()
    data_monitor_worker.update_central_bank_open_market_operation()
    data_monitor_worker.update_lpr_biding_change()


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
    schedule.every(5).minutes.do(update_news)
    schedule.every(5).minutes.do(update_notification)

    run_continuously(5 * 60)