'''
    数据变动监听
'''
from src.service.DataWorker import DataWorker
from src.service.NotificationService import NotificationService
from src.service.LogService import LogService


class DataMonitorWorker:

    def update_cnn_fear_greed_index(self):
        title = 'CNN恐慌指数更新'

        try:
            index_model = DataWorker.get_cnn_fear_greed_index()

            model = {
                "title": title,
                "description": '最新指数为: ' + str(index_model['now']),
                "raw": index_model
            }

            NotificationService.add('cnn_fear_greed_index', model)
        except Exception as e:
            print(e)
            LogService.error(title, e)

    def update_american_securities_yield(self):
        title = '美债收益率倒挂'

        try:
            yield_model = DataWorker.get_american_securities_yield()
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
                "title": title,
                "description": content,
                "raw": yield_model
            }

            if len(content) > 0:
                NotificationService.add('american_securities_yield', model)
        except Exception as e:
            print(e)
            LogService.error(title, e)

    def update_central_bank_open_market_operation(self):
        title = '央行公开市场操作'

        try:
            operation_list = DataWorker.get_latest_central_bank_open_market_operation()
            for operation in operation_list:
                model = {
                    "title": title,
                    "description": operation['html'],
                    "html": True,
                    "raw": operation
                }

                NotificationService.add('central_bank_open_market_operation', model)
        except Exception as e:
            print(e)
            LogService.error(title, e)

    def update_lpr_biding_change(self):
        title = 'LPR报价变动'
        try:
            biding = DataWorker.get_latest_lpr_biding()
            model = {
                "title": title,
                "html": True,
                "description": '<p>1年: ' + str(biding['data']['1Y']) + '%</p><p>5年: ' + str(biding['data']['5Y']) + '%</p>',
                "raw": biding
            }
            NotificationService.add('lrp_biding', model)
        except Exception as e:
            print(e)
            LogService.error(title, e)

    # 获取休市日期数据
    def update_market_suspend_notice(self):
        title = '休市日期提醒'
        try:
            notice_list = DataWorker.get_suspend_notice()
            for notice in notice_list:
                model = {
                    "title": title,
                    "description": notice['title'],
                    "url": notice['url'],
                    "raw": notice
                }
                NotificationService.add('market_suspend_date', model)
        except Exception as e:
            print(e)
            LogService.error(title, e)


if __name__ == '__main__':
    DataMonitorWorker().update_market_suspend_notice()