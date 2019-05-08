from src.utils.sessions import FuturesSession
import json
import time
from src.service.stockService import StockService
session = FuturesSession(max_workers=50)

client = StockService.getMongoInstance()
database = client.geekbang
historyDocument = database.zuoertingfeng

cookies = {
    "GCESS": "BAsCBAAEBAAvDQAJAQEIAQMHBN899ZsKBAAAAAABBEYdEgACBBaY0lwMAQEGBHY8pzAFBAAAAAADBBaY0lw-",
    "GCID": "f9d2cdd-72b2df1-0278824-3e979b7",
}

headers = {
    'Content-Type': 'application/json',
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36",
    "Host": "time.geekbang.org",
    "Origin": "https://time.geekbang.org",
    "Accept": "application/json, text/plain, */*"
}

def getCategory(cid):
    url = "https://time.geekbang.org/serv/v1/column/articles"

    data = {
        "cid": cid,
        "order": 'earliest',
        "prev": 0,
        "sample": False,
        "size": 100
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

if __name__ == '__main__':
    categoryResponse = resolveResult(getCategory(48))
    categoryList = categoryResponse["data"]["list"]
    for category in categoryList:
        time.sleep(1)
        categoryId = category["id"]
        columnResponse = resolveResult(getColumn(categoryId))
        columnDetail = columnResponse["data"]
        historyDocument.update({"cid": categoryId }, columnDetail, True)