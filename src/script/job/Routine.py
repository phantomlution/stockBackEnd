'''
    每日的任务调度
'''
from src.script.job.MarketCapitalDataJob import MarketCapitalDataJob
from src.script.job.StockBaseDataJob import StockBaseDataJob
from src.script.job.StockNoticeJob import StockNoticeJob
from src.script.job.StockThemeDataJob import StockThemeDataJob
from src.script.job.StockTradeDataJob import StockTradeDataJob
from src.script.job.JobScheduler import JobScheduler


if __name__ == '__main__':

    pending_task = [
        # 'StockBaseDataJob', # 数据库初始化时需要调用 TODO 寻找新的数据源
        # 'MarketCapitalDataJob',
        'StockTradeDataJob',
        # 'StockThemeDataJob',
        # 'StockNoticeJob'
    ]

    JobScheduler(pending_task, locals()).start()
