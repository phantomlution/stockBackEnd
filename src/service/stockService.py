from pymongo import MongoClient


class StockService(object):

    @staticmethod
    def getMongoInstance():
        return MongoClient('mongodb://localhost:27017')
