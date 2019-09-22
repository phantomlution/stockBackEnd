from pymongo import MongoClient


class StockService(object):

    client = MongoClient('mongodb://localhost:27017')

    @staticmethod
    def getMongoInstance(cls):
        return cls.client
