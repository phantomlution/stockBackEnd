'''
    数据变动监听
'''
from src.service.DataService import DataService
from src.service.NotificationService import NotificationService


class DataMonitorWorker:

    def update_cnn_fear_greed_index(self):
        model = {
            "title": 'CNN恐慌指数更新'
        }
        try:
            index_model = DataService.get_cnn_fear_greed_index()
            model["description"] = '最新指数为: ' + str(index_model['now'])
            model["raw"] = index_model
            NotificationService.add('cnn_fear_greed_index', model)
        except Exception as e:
            print(e)
            NotificationService.fail(model['title'], e)

    def update_american_securities_yield(self):
        model = {
            "title": '美债收益率倒挂'
        }
        try:
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

            model["description"] = content
            model["raw"] = yield_model

            if len(content) > 0:
                NotificationService.add('american_securities_yield', model)
        except Exception as e:
            print(e)
            NotificationService.fail(model['title'], e)

    def update_central_bank_open_market_operation(self):
        model = {
            "title": '央行公开市场操作'
        }
        try:
            operation_list = DataService.get_latest_central_bank_open_market_operation()
            for operation in operation_list:
                model["description"] = operation['html']
                model["html"] = True
                model["raw"] = operation
                NotificationService.add('central_bank_open_market_operation', model)
        except Exception as e:
            print(e)
            NotificationService.fail(model['title'], e)

    def update_lpr_biding_change(self):
        model = {
            "title": 'LPR报价变动'
        }
        try:
            biding = DataService.get_latest_lpr_biding()
            model["html"] = True
            model["description"] = '<p>1年: ' + str(biding['data']['1Y']) + '%</p><p>5年: ' + str(biding['data']['5Y']) + '%</p>'
            model["raw"] = biding
            NotificationService.add('lrp_biding', model)
        except Exception as e:
            print(e)
            NotificationService.fail(model['title'], e)


if __name__ == '__main__':
    DataMonitorWorker().update_cnn_fear_greed_index()