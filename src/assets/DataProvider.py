import json
import os

class DataProvider:

    def load_json_file(self, file_path):
        with open(file_path) as json_file:
            data = json.load(json_file)
            return data

    def load_shanghai_stock(self):
        return self.load_json_file(os.path.dirname(__file__) + '/shanghai.json')

    def load_shenzhen_stock(self):
        return self.load_json_file(os.path.dirname(__file__) + '/shenzhen.json')

    '''
        获取股票数据
    '''
    def get_stock_list(self):
        result = []
        for stock in list(self.load_shanghai_stock()):
            result.append({
                "name": str.strip(stock["name"]),
                "code": 'SH' + str.strip(stock['code'])
            })

        for stock in list(self.load_shenzhen_stock()):
            result.append({
                "name": str.strip(stock["name"]),
                "code": 'SZ' + str.strip(stock['code'])
            })

        return result[:20]

