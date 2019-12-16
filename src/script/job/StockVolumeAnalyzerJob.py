'''
    股票交易量分析
'''
from src.service.StockService import StockService
client = StockService.getMongoInstance()
history_document = client.stock.history


def calculate_average_amount(item_list, recent_count):
    data_list = item_list[-1 * recent_count:]
    total = 0
    for data in data_list:
        total += data[6]
    average = total / len(data_list)
    return round(average / 10000 / 10000, 2)


if __name__ == '__main__':
    # StockVolumeAnalyzerJob().run()
    # temporary_patch()
    code = 'SZ002482'
    target_date = '2019-06-25'

    history_data = history_document.find_one({ "code": code })['data']
    old_history_data = list(filter(lambda item: item[0] <= target_date, history_data))
    print(calculate_average_amount(old_history_data, 30))
    print(calculate_average_amount(old_history_data, 60))
    print(calculate_average_amount(old_history_data, 90))




