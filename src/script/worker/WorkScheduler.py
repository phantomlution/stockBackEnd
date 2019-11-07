from src.script.worker.DataMonitorWorker import DataMonitorWorker
from src.script.worker.NewsScratchWorker import NewsScratchWorker
import time
import schedule


def init_task():
    data_monitor_worker = DataMonitorWorker()
    schedule.every(25).minutes.do(data_monitor_worker.update_cnn_fear_greed_index)
    schedule.every(25).minutes.do(data_monitor_worker.update_american_securities_yield)
    schedule.every(25).minutes.do(data_monitor_worker.update_central_bank_open_market_operation)
    schedule.every(25).minutes.do(data_monitor_worker.update_lpr_biding_change)

    news_scratch_worker = NewsScratchWorker()
    schedule.every(30).minutes.do(news_scratch_worker.get_cnbc_news)
    schedule.every(30).minutes.do(news_scratch_worker.get_financial_times_news)
    schedule.every(30).minutes.do(news_scratch_worker.get_central_bank_communication_news)
    schedule.every(30).minutes.do(news_scratch_worker.get_foreign_affair_news)
    schedule.every(30).minutes.do(news_scratch_worker.get_development_revolution_committee_news)
    schedule.every(30).minutes.do(news_scratch_worker.get_prc_board_meeting_news)
    schedule.every(30).minutes.do(news_scratch_worker.get_prc_collective_learning_news)


if __name__ == '__main__':
    init_task()

    while True:
        schedule.run_pending()
        time.sleep(1)


