from src.utils.db import MySQL

class StockService(object):

    @staticmethod
    def get_stock_list():
        mysql = MySQL()
        result = mysql.findAll('select * from stock where skip=0 and black_list = 0', ())
        mysql.close()
        return result
