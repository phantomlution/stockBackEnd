'''
    数据变动监听
'''
from src.service.StockService import StockService
from src.service.DataService import DataService
client = StockService.getMongoInstance()
notification_document = client.stock.notification


class DataMonitorWorker:

    def update_cnn_fear_greed_index(self):
        index_model = DataService.get_cnn_fear_greed_index()





if __name__ == '__main__':
    DataMonitorWorker().get_cnn_fear_greed_index()