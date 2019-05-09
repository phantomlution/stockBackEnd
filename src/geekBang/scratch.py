from src.utils.sessions import FuturesSession
import json
import time
from src.service.stockService import StockService
session = FuturesSession(max_workers=50)

client = StockService.getMongoInstance()
database = client.geekbang


cookies = {
    "GCESS": "BAYEO.LjoQoEAAAAAAcEP8.4rQUEAAAAAAMEBJfTXAQEAC8NAAIEBJfTXAgBAwsCBAABBEYdEgAMAQEJAQE-",
    "GCID": "a865c14-aeb2edc-c6dab38-71a7d6e",
}

headers = {
    'Content-Type': 'application/json',
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36",
    "Host": "time.geekbang.org",
    "Origin": "https://time.geekbang.org",
    "Accept": "application/json, text/plain, */*"
}

def getCategory(cid):
    url = "https://time.geekbang.org/serv/v1/column/details"

    data = {
        "ids": [cid],
        "is_article": 1
    }
    return session.post(url, data=json.dumps(data), headers=headers, cookies=cookies)

def getColumn(id):
    data = {
        "id": id,
        "include_neighbors": True
    }
    url = 'https://time.geekbang.org/serv/v1/article'

    return session.post(url, data=json.dumps(data), headers=headers, cookies=cookies)

def resolveResult(response):
    print(response.result())
    return json.loads(response.result().content.decode())

# 重学前端 154
# 左耳 48

id_list = [
    176,175,170,169,167,166,165,164,163,161,
    160,159,158,156,155,154,153,129,148,147,
    145,143,142,140,139,138,133,132,130,127,
    126,116,115,113,112,111,110,108,105,104,
    103,100,98,97,87,85,84,82,81,80,
    79,77,76,75,74,73,66,63,62,61,
    50, 49, 48, 43, 42
]

def synchornizeColumn(directoryId):
    categoryResponse = resolveResult(getCategory(directoryId))
    categoryResponse = categoryResponse["data"][0]
    if categoryResponse is not None:
        database.directory.update({"id": directoryId}, categoryResponse, True)
        for category in categoryResponse["list"]:
            categoryId = category["id"]
            columnResponse = resolveResult(getColumn(categoryId))
            columnDetail = columnResponse["data"]
            database.column.update({"id": columnDetail["id"]}, columnDetail, True)

if __name__ == '__main__':
    count = 0
    for directoryId in id_list:
        print('current is' + str(id_list[count]))
        synchornizeColumn(directoryId)
        count += 1
