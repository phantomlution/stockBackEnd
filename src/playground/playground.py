from src.service.HtmlService import get_response
import json
from src.service.StockService import StockService
import time
# 295,2509,2517,2519,2544,2671
lid = '2509'

client = StockService.getMongoInstance()

for idx in range(50):
    page = idx + 1
    print(page)
    url = 'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=' + lid + '&k=&num=50&page=' + str(page)
    response = get_response(url)
    response_json = json.loads(response)
    data_list = response_json['result']['data']
    for item in data_list:
        client.stock.sina.insert(item)
    time.sleep(1)