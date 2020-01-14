'''
    给其他 service 提供数据库数据
'''

from pymongo import MongoClient

mongo_instance = MongoClient('mongodb://localhost:27017')

base_document = mongo_instance.stock.base
notice_document = mongo_instance.stock.notice
history_document = mongo_instance.stock.history
stock_pool_document = mongo_instance.stock.stock_pool
concept_block_ranking_document = mongo_instance.stock.concept_block_ranking


class DatabaseService:

    @staticmethod
    def get_mongo_instance():
        return mongo_instance

    @staticmethod
    def get_history_data(code):
        item = history_document.find_one({"symbol": code}, {"_id": 0})
        if item is None:
            return None
        return item['list']

    @staticmethod
    def get_base(code):
        item = base_document.find_one({'symbol': code})
        if item is None:
            raise Exception('找不到对应的信息{}'.format(code))
        item['_id'] = str(item['_id'])
        return item

    @staticmethod
    def get_base_item_list():
        return base_document.find({}, {"symbol": 1, "name": 1, 'type': 1})

    @staticmethod
    def get_concept_block_ranking(date_list):
        if len(date_list) == 0:
            return []

        return list(concept_block_ranking_document.find({ 'date': { '$in': date_list } }, { '_id': 0 }))