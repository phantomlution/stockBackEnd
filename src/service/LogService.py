'''
    简单记录错误日志
'''

from src.utils.date import get_current_datetime_str
from src.service.StockService import StockService

client = StockService.getMongoInstance()
log_document = client.stock.log


class LogService:

    @staticmethod
    def error(title, exception):
        model = {
            "type": 'error',
            "title": title,
            "description": '执行失败',
            "exception": str(exception),
            'created_time': get_current_datetime_str()
        }
        log_document.insert(model)
