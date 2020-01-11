import tushare
import json
from src.service.StockService import StockService
from src.utils.lodash import lodash

client = StockService.getMongoInstance()
index_document = client.stock.sync_index

# tushare_token = 'bcbaeb905d1633b6a8c84c837699cdacbefcfe713d07f42fcbe0e694'


# 后去分时实时成交数据
def get_history_fragment_trade_data(code, date):
    return _get_stock_history_fragment_trade(code, date)


def _get_stock_history_fragment_trade(code, date):
    base = StockService.get_stock_base(code)
    if base is None:
        raise Exception('code异常')

    _type = base['type']

    if _type == 'stock':
        try:
            data_frame = tushare.get_tick_data(base['code'], date=date, src='tt')
        except Exception as e:
            print(e)
            return None
        if data_frame is None:
            return None
        return json.loads(data_frame.to_json(orient="records"))
    else:
        document = client.stock['sync_' + _type]
        record = document.find_one({ "symbol": base['symbol'], "date": date }, {'_id': 0})
        if record is None:
            return []
        else:
            # 补充change字段，用于其他地方计算pre_close
            pre_close = record['pre_close']
            data = record['data']

            for idx, item in enumerate(data):
                item['time'] = item['time'] + ':00'
                if idx == 0:
                    item['change'] = item['price'] - pre_close
                else:
                    item['change'] = item['price'] - data[idx - 1]['price']

            return data


# 获取实时分时数据
def get_real_time_trade_data(code):
    try:
        data_frame = tushare.get_today_ticks(code)
    except Exception as e:
        print(e)
        return None
    return json.loads(data_frame.to_json(orient='records'))
