'''
    获取新闻
'''
from src.service.StockService import StockService


client = StockService.getMongoInstance()
news_document = client.stock.news


class NewsService:

    @staticmethod
    def paginate(query={}, page_no=1, page_size=50):
        # python sort 要传入 tuple 数组
        news_list = list(news_document.find(query, { "_id": 0}).sort([('publish_date', -1 ), ("create_date", -1)]))

        return {
            "page_no": page_no,
            "page_size": page_size,
            "list": news_list,
            "total": len(news_list)
        }