from src.service.DatabaseService import DatabaseService
from src.service.DataService import DataService
from src.service.AnalyzeService import AnalyzeService
mongo = DatabaseService.get_mongo_instance()

surge_for_short_document = mongo.stock.surge_for_short
heat_report_document = mongo.stock.heat_report
base_document = mongo.stock.base


# 提取指定日期内的有效拉高出货点
def get_target_date_surge_for_short_result():
    date_list = ['2020-01-13', '2020-01-14']
    item_list = DatabaseService.get_base_item_list()

    result = []
    for item in item_list:
        _type = item['type']
        if _type == 'stock':
            code = item['symbol']
            analyze_result = {
                'code': item['symbol'],
                "name": item['name'],
                'list': []
            }
            for _date in date_list:
                short_item = surge_for_short_document.find_one({ 'date': _date, 'code': code })
                if short_item is not None:
                    if len(short_item['time']) > 0:
                        analyze_result['list'].append({
                            "date": _date
                        })
            if len(analyze_result['list']) > 0:
                result.append(analyze_result)

    return result


# 生成热度报告
def generate_heat_report():
    stock_list = list(base_document.find({ 'type': 'stock' }))
    count = 0
    for item in stock_list:
        count += 1
        print('{}/{}'.format(count, len(stock_list)))
        code = item['symbol']

        if heat_report_document.find_one({ 'code': code}) is not None:
            continue

        history = DatabaseService.get_history_data(code)
        model = {
            'code': code,
            'name': item['name'],
            'total': 0,
            'count': 0
        }
        for history_item in history[-200:]:
            _date = history_item['date']
            try:
                surge_result = AnalyzeService.get_surge_for_short(code, _date)
            except Exception as e:
                surge_result = None
            if surge_result is not None and len(surge_result['time']):
                model['count'] += 1
            model['total'] += 1
        heat_report_document.update({ 'code': model['code']}, model, True)


if __name__ == '__main__':
    generate_heat_report()
