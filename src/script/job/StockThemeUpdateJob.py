'''
    更新股票相关的主题信息
    1. 股票 base
    2. 主题列表
'''
from src.script.job.Job import Job
from src.service.StockService import StockService
from src.assets.DataProvider import DataProvider

client = StockService.getMongoInstance()
base_document = client.stock.base
theme_document = client.stock.theme
theme_market_document = client.stock.theme_market


class StockThemeUpdateJob:
    def __init__(self):
        stock_list = DataProvider().get_stock_list()
        self.job = Job(name='股票-主题更新')
        self.market_map = {}
        for stock in stock_list:
            self.job.add(stock)

    def synchronize_update_stock_theme(self, code):
        stock_theme_item = theme_document.find_one({ "code": code })
        if stock_theme_item is None:
            stock_theme_list = []
        else:
            stock_theme_list = stock_theme_item['theme']

        stock_base = base_document.find_one({ "symbol": code })

        if stock_base is None:
            raise Exception('数据异常: {}'.format(code))

        base_document.update({ 'symbol': code }, { '$set': {'theme_list': stock_theme_list } }, True)

        for theme_item in stock_theme_list:
            if theme_item not in self.market_map:
                self.market_map[theme_item] = []

            self.market_map[theme_item].append({
                "code": code,
                "name": stock_base['name']
            })

    def update_stock_market(self):
        theme_market_document.drop()
        for theme_name in self.market_map:
            model = {
                "name": theme_name,
                "list": self.market_map[theme_name]
            }
            theme_market_document.update({ "name": model["name"]}, model, True)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        for task_index, task in enumerate(self.job.task_list):
            stock = task['raw']
            task_id = task["id"]
            code = stock.get('code')
            self.synchronize_update_stock_theme(code)
            if task_index == len(self.job.task_list) - 1:
                self.update_stock_market()

            self.job.success(task_id)


if __name__ == '__main__':
    StockThemeUpdateJob().run()