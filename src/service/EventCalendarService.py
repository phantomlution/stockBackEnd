from src.service.StockService import StockService

client = StockService.getMongoInstance()
event_calendar_document = client.stock.event_calendar


class EventCalendarService:

    @staticmethod
    def add_item(model):
        event_calendar_document.insert(model)

    @staticmethod
    def get_item_list():
        return list(event_calendar_document.find({}, { "_id": 0 }))
