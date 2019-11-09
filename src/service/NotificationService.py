from src.service.StockService import StockService
from src.utils.date import get_current_datetime_str
import uuid

client = StockService.getMongoInstance()
notification_document = client.stock.notification


class NotificationService:

    @staticmethod
    def add(key, model):
        # raw 主要用于数据快照
        if 'raw' not in model:
            raise Exception('raw 未定义')
        raw = model['raw']

        if 'id' not in raw:
            raise Exception('id 未定义')

        model['key'] = key
        model['id'] = raw['id']
        if 'release_date' in raw:
            model['release_date'] = raw['release_date']
        model['created'] = get_current_datetime_str()
        model['has_read'] = False

        if notification_document.find_one({"key": key, "id": model["id"]}) is None:
            notification_document.insert(model)

    @staticmethod
    def fail(title, exception):
        model = {
            "title": title,
            "description": '执行失败',
            "raw": {
                "id": get_current_datetime_str() + '_' + str(uuid.uuid4()),
                "exception": str(exception)
            }
        }
        return NotificationService.add('execute_failed', model)