'''
    获取股票交易数据
'''
from src.script.job.Job import Job
from src.utils.sessions import FuturesSession
from src.service.StockService import StockService
from src.service.EastMoneyService import EastMoneyService
from src.utils.lodash import lodash
import asyncio

client = StockService.getMongoInstance()
history_document = client.stock.history
session = FuturesSession(max_workers=1)


class StockTradeDataJob:
    def __init__(self):
        base_list = StockService.get_all_item()
        self.job = Job(name='交易数据同步')
        for base in base_list:
            self.job.add(base)

    def update_trade_data(self, base):
        model = {
            "symbol": base['symbol'],
            "name": base['name'],
            "type": base['type']
        }
        if 'secid' in base:
            secid = base['secid']
            model['list'] = EastMoneyService.get_kline(secid)
            history_document.update({ "symbol": base['symbol']}, model, True)
        elif base['type'] in 'capital':
            # 手动生成kline
            document = client.stock['sync_capital']
            item_list = document.find({ "symbol": base['symbol'] }).sort([('date', -1)]).limit(200)
            if base['symbol'] == 'CAPITAL.NORTH':
                hu_gu_tong_history = EastMoneyService.get_hu_gu_tong_hot_money()
                shen_gu_tong_history = EastMoneyService.get_shen_gu_tong_hot_money()
            elif base['symbol'] == 'CAPITAL.SOUTH':
                hu_gu_tong_history = EastMoneyService.get_gang_gu_tong_hu_hot_money()
                shen_gu_tong_history = EastMoneyService.get_gang_gu_tong_shen_hot_money()

            result = []
            for item in item_list:
                _date = item['date']

                hu_gu_tong_item = lodash.find(hu_gu_tong_history, lambda _item: _item['date'] == _date)
                if hu_gu_tong_item is None:
                    raise Exception('沪股通历史数据异常')
                shen_gu_tong_item = lodash.find(shen_gu_tong_history, lambda _item: _item['date'] == _date)
                if shen_gu_tong_item is None:
                    raise Exception('深股通数据异常')

                pre_close = hu_gu_tong_item['pre_close'] + shen_gu_tong_item['pre_close']

                price_list = item['data']
                for price_item in price_list:
                    price_item['total'] = pre_close + price_item['huAmount'] + price_item['shenAmount']
                    # 对齐数据格式
                    price_item['price'] = price_item['total']
                    price_item['amount'] = None

                max_item = lodash.max_by(price_list, lambda _item: _item['total'])
                min_item = lodash.min_by(price_list, lambda _item: _item['total'])

                if 'pre_close' not in item:
                    # 反向补齐之前的旧数据
                    item['pre_close'] = pre_close
                    document.update({ "_id": item['_id']}, item)

                kline_item = {
                    "date": item['date'],
                    "max": max_item['total'],
                    'min': min_item['total'],
                    "open": price_list[0]['total'],
                    'close': price_list[-1]['total'],
                    "pre_close": pre_close,
                    'amount': hu_gu_tong_item['amount'] + shen_gu_tong_item['amount']
                }
                result.append(kline_item)
            EastMoneyService.generate_pre_close(result)
            model['list'] = result
            history_document.update({ "symbol": base['symbol']}, model, True)
        else:
            raise Exception('code错误{code}'.format(code=base['symbol']))

    async def asynchronize_load_trade_data(self, task_id, base):
        # time.sleep(0.3)
        try:
            self.update_trade_data(base)
            self.job.success(task_id)
        except Exception as e:
            print(e)
            self.job.fail(task_id, e)

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        history_document.drop()
        loop = asyncio.get_event_loop()
        for task in self.job.task_list:
            base = task['raw']
            task_id = task["id"]
            loop.run_until_complete(self.asynchronize_load_trade_data(task_id, base))


if __name__ == '__main__':
    stock_code = 'CAPITAL.NORTH'
    base = StockService.get_stock_base(stock_code)
    print(StockTradeDataJob().update_trade_data(base))
    # print(StockTradeDataJob().run())