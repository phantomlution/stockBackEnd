'''
    获取新闻
'''
from src.service.StockService import StockService
import bson


client = StockService.getMongoInstance()
news_document = client.stock.news


class NewsService:

    @staticmethod
    def mark_subscribe(_id, subscribe):
        object_id = bson.ObjectId(_id)
        news_document.update({ "_id": object_id }, { '$set': { 'subscribe': bool(subscribe) }})

    @staticmethod
    def mark_read(_id):
        object_id = bson.ObjectId(_id)
        news_document.update({ "_id": object_id }, { '$set': { "has_read": True, 'subscribe': False } })

    @staticmethod
    def paginate(query, page_no=1, page_size=50, limit=0):
        # python sort 要传入 tuple 数组
        result = list(news_document.find(query).sort([('subscribe', -1 ), ("create_date", -1)]).limit(limit))
        news_list = []
        for item in result:
            item['_id'] = str(item['_id'])
            news_list.append(item)

        return {
            "page_no": page_no,
            "page_size": page_size,
            "list": news_list,
            "total": len(news_list)
        }