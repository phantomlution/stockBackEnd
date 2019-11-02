tushare_token = 'bcbaeb905d1633b6a8c84c837699cdacbefcfe713d07f42fcbe0e694'
import tushare
import json

# 后去分时实时成交数据
def get_history_fragment_trade_data(code, date):
    try:
        data_frame = tushare.get_tick_data(code, date=date, src='tt')
    except Exception as e:
        print(e)
        return None
    if data_frame is None:
        return None
    return json.loads(data_frame.to_json(orient="records"))