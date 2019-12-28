'''
    市场预测以及复盘
'''

from src.service.StockService import StockService

client = StockService.getMongoInstance()
chess_document = client.stock.chess


class ChessService:

    @staticmethod
    def get_item(_date):
        chess_item = chess_document.find_one({ 'date': _date }, { '_id': 0 })
        if chess_item is None:
            chess_item = {
                "date": _date,
                "predict": '',
                "replay": ''
            }
        elif 'predict' not in chess_item:
            chess_item['predict'] = ''
        elif 'replay' not in chess_item:
            chess_item['replay'] = ''

        return chess_item

    @staticmethod
    def update_predict(_date, content):
        return ChessService.update_item(_date, 'predict', content)

    @staticmethod
    def update_replay(_date, content):
        return ChessService.update_item(_date, 'replay', content)

    @staticmethod
    def update_item(_date, field, content):
        model = {}
        model[field] = content
        chess_document.update({ 'date': _date }, { "$set": model}, True)