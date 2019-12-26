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
from src.script.job.StockSubCompanyUpdateJob import StockSubCompanyUpdateJob
from src.script.job.StockRestrictSellUpdateJob import StockRestrictSellUpdateJob
from src.script.job.DatabaseBackUpJob import DatabaseBackUpJob
from src.script.job.StockConceptBlockRanking import StockConceptBlockRanking
from src.script.job.FinancialCalendarJob import FinancialCalendarJob
from src.script.job.JobScheduler import JobScheduler


def get_init_routine():
    return [
        'StockBaseDataJob',  # 数据库初始化时需要调用
        # 'StockRestrictSellUpdateJob', # 关联所有相关限售股份
        # "StockSubCompanyUpdateJob", # 关联子公司
    ]


def get_theme_routine():
    return [
        'StockThemeDataJob',
        'StockThemeUpdateJob',  # 更新主题相关信息
    ]


def get_daily_routine():
    return [
        'MarketCapitalDataJob',  # 同步当日资金走势
        'FinancialCalendarJob',  # 同步财经日历
        "BondDataJob",  # 更新债券信息数据源
        "BondRiskDataJob",  # 更新债券重大事项数据源
        'StockNoticeJob',
        "StockBondNoticeUpdateJob",  # 将债券发行数据和债券风险项同步到 基础信息中
        "StockPoolDailyUpdateJob",  # 同步股票的重大事项
        "StockConceptBlockRanking",  # 同步概念板块排行榜
        'DatabaseBackUpJob',
        'StockTradeDataJob',
    ]


if __name__ == '__main__':

    pending_task = []

    # pending_task += get_init_routine()
    # pending_task += get_theme_routine()
    pending_task += get_daily_routine()

    JobScheduler(pending_task, locals()).start()
