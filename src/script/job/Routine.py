'''
    每日的任务调度
'''
from src.script.job.MarketCapitalDataJob import MarketCapitalDataJob
from src.script.job.StockBaseDataJob import StockBaseDataJob
from src.script.job.StockNoticeJob import StockNoticeJob
from src.script.job.StockThemeDataJob import StockThemeDataJob
from src.script.job.StockThemeUpdateJob import StockThemeUpdateJob
from src.script.job.StockTradeDataJob import StockTradeDataJob
from src.script.job.BondDataJob import BondDataJob
from src.script.job.BondRiskDataJob import BondRiskDataJob
from src.script.job.StockBondNoticeUpdateJob import StockBondNoticeUpdateJob
from src.script.job.StockPoolDailyUpdateJob import StockPoolDailyUpdateJob
from src.script.job.JobScheduler import JobScheduler


if __name__ == '__main__':

    pending_task = [
        # 'StockBaseDataJob', # 数据库初始化时需要调用
        # 'StockThemeDataJob',
        # 'StockThemeUpdateJob', # 更新主题相关信息
        # 'MarketCapitalDataJob',
        # "BondDataJob", # 更新债券信息数据源
        # "BondRiskDataJob", # 更新债券重大事项数据源
        # 'StockNoticeJob',
        # "StockBondNoticeUpdateJob", #  将债券发行数据和债券风险项同步到 基础信息中
        "StockPoolDailyUpdateJob",  # 同步股票的重大事项
        'StockTradeDataJob',

    ]

    JobScheduler(pending_task, locals()).start()
