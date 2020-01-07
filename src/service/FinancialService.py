import tushare
import json
from src.service.StockService import StockService
from src.utils.lodash import lodash

client = StockService.getMongoInstance()
index_document = client.stock.sync_index

# tushare_token = 'bcbaeb905d1633b6a8c84c837699cdacbefcfe713d07f42fcbe0e694'


# 后去分时实时成交数据
def get_history_fragment_trade_data(code, date):
    # 跳过上证指数
    if code == 'SH000001':
        return get_native_index_fragment_trade_data('1.000001', date)

    code = code[2:]
    try:
        data_frame = tushare.get_tick_data(code, date=date, src='tt')
    except Exception as e:
        print(e)
        return None
    if data_frame is None:
        return None
    return json.loads(data_frame.to_json(orient="records"))


# 获取实时分时数据
def get_real_time_trade_data(code):
    try:
        data_frame = tushare.get_today_ticks(code)
    except Exception as e:
        print(e)
        return None
    return json.loads(data_frame.to_json(orient='records'))


# 获取本地缓存的指数数据
def get_native_index_fragment_trade_data(secid, date):
    record = index_document.find_one({ "secid": secid, "date": date })
    if record is None:
        return None

    pre_close = record['pre_close']
    data = record['data']

    for idx, item in enumerate(data):
        item['time'] = item['time'][:5]
        if idx == 0:
            item['change'] = item['price'] - pre_close
        else:
            item['change'] = item['price'] - data[idx - 1]['price']

    return data
