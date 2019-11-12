from src.service.StockService import StockService
from bson import ObjectId
client = StockService.getMongoInstance()

custom_event_document = client.stock.custom_event
custom_event_item_document = client.stock.custom_event_item


class CustomEventService:

    @staticmethod
    def get_custom_event_list():
        # 返回所有的自定义事件
        event_list = custom_event_document.find({ "archive": False })
        result = []
        for event in event_list:
            event['_id'] = str(event['_id'])
            result.append(event)

        return result

    @staticmethod
    def save_event(event_name):
        if custom_event_document.find_one({ "name": event_name }) is not None:
            raise Exception('该事件已存在')
        model = {
            "name": event_name,
            "archive": False # 是否归档
        }
        result = custom_event_document.insert(model)
        return str(result)

    @staticmethod
    def get_custom_event(event_id):
        event = custom_event_document.find_one({ "_id": ObjectId(event_id) })
        if event is None:
            raise Exception('该事件不存在')

        if 'content' not in event:
            event['content'] = ''

        return {
            "_id": str(event['_id']),
            "name": event['name'],
            "content": event['content'],
            "item_list": CustomEventService.get_custom_event_item_list(event_id)
        }

    @staticmethod
    def get_custom_event_item_list(event_id):
        result = []
        item_list = custom_event_item_document.find({ "event_id": event_id }).sort([('time', 1)])
        for item in item_list:
            item['_id'] = str(item['_id'])
            result.append(item)
        return result

    @staticmethod
    def save_event_item(item):
        event_type = item['type']
        if event_type == 'stock':
            event_id = 'stock_' + item['stockCode']
        else:
            event_id = item['eventId']
        model = {
            'event_id': event_id,
            "time": item['time'],
            'content': item['content'],
            "type": event_type,
            "url": item['url']
        }

        custom_event_item_document.insert(model)