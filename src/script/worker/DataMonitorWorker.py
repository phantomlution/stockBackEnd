'''
    数据变动监听
'''
from src.service.StockService import StockService
from src.service.DataService import DataService
from src.utils.date import get_current_datetime_str
client = StockService.getMongoInstance()
notification_document = client.stock.notification

update_config = {
    'cnn_fear_greed_index'
}


class DataMonitorWorker:

    def add_notification(self, key, model):
        # raw 主要用于数据快照
        raw = model['raw']

        model['key'] = key
        model['id'] = raw['id']
        model['release_date'] = raw['release_date']
        model['created'] = get_current_datetime_str()
        model['has_read'] = False

        if notification_document.find_one({ "key": key, "id": model["id"] }) is None:
            notification_document.insert(model)

    def update_cnn_fear_greed_index(self):
        index_model = DataService.get_cnn_fear_greed_index()
        model = {
            "title": 'CNN恐慌指数更新',
            "description": '最新指数为: ' + str(index_model['now']),
            "raw": index_model
        }
        self.add_notification('cnn_fear_greed_index', model)

    def update_american_securities_yield(self):
        yield_model = DataService.get_american_securities_yield()
        biding = yield_model['data']
        ten_year_biding = biding['10Y']

        if biding['1M'] >= ten_year_biding:
            content = '1个月收益率与10年倒挂'
        elif biding['3M'] >= ten_year_biding:
            content = '3个月收益率与10年倒挂'
        elif biding['6M'] >= ten_year_biding:
            content = '6个月收益率与10年倒挂'
        else:
            content = ''

        model = {
            "title": '美债收益率倒挂',
            "description": content,
            "raw": yield_model
        }

        if len(content) > 0:
            self.add_notification('american_securities_yield', model)

    def update_central_bank_open_market_operation(self):
        operation_list = DataService.get_latest_central_bank_open_market_operation()
        for operation in operation_list:
            model = {
                "title": '央行公开市场操作',
                "description": operation['html'],
                "html": True,
                "raw": operation
            }
            self.add_notification('central_bank_open_market_operation', model)

    def update_lpr_biding_change(self):
        biding = DataService.get_latest_lpr_biding()
        model = {
            "title": "LPR报价变动",
            "html": True,
            "description": '<p>1年: ' + str(biding['data']['1Y']) + '%</p><p>5年: ' + str(biding['data']['5Y']) + '%</p>',
            "raw": biding
        }
        self.add_notification('lrp_biding', model)


if __name__ == '__main__':
    DataMonitorWorker().update_central_bank_open_market_operation()