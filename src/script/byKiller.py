import datetime
import numpy as np
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import itchat
from src.service.stockService import StockService
from src.utils.sessions import FuturesSession
import asyncio

FILE_HELPER = 'filehelper'

null = None
timeformat = '%Y-%m-%d'

SHOW_DETAIL = False

client = StockService.getMongoInstance()
database = client.stock
historyDocument = database.history

session = FuturesSession(max_workers=50)

fetch_cookie_url = 'https://xueqiu.com/S/SZ000007'

cookies = {}

def loadToken():
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(chrome_options=options)
    driver.get(fetch_cookie_url)
    local_cookies = driver.get_cookies()
    cookie_fields_set = set([
        'xq_a_token',
        'xq_a_token.sig',
        'xq_r_token',
        'xq_r_token.sig'
    ])
    for cookie in local_cookies:
        cookie_name = cookie['name']
        cookie_value = cookie['value']
        if cookie_name in cookie_fields_set:
            cookies[cookie_name] = cookie_value
    driver.quit()


# make sure your token is valid
def refreshToken():
    loadToken()

refreshToken()

print('123')
print(cookies)

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Origin': 'https://xueqiu.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
}

def loadJsonFile(filePath):
    with open(filePath) as json_file:
        data = json.load(json_file)
        return data

blackListSet = set(loadJsonFile('../assets/blackList.json'))

@itchat.msg_register([itchat.content.TEXT])
def text_reply(msg):
    content = msg['Content']
    toUserName = msg['ToUserName']
    if toUserName == FILE_HELPER:
        if content == '导出':
            pushMessage('正在导出中')
            synchronizeStockData(True)
        else:
            result = calculateBiKiller('SZ000007', 420)
            pushMessage(result['brief'])

def numberFormat(num):
    return '%.2f' % num



def wechatMsgResponse(msg):
    return msg

def pushMessage(msg):
    itchat.send(msg, toUserName=FILE_HELPER)

def getStockBase(code):
    url = 'https://stock.xueqiu.com/v5/stock/quote.json?symbol=' + str(code)

    return json.loads(session.get(url, headers=headers, cookies=cookies).result().content.decode())

def getHistoryData(code, days):
    session.head('https://xueqiu.com/S/' + code)

    url = 'https://stock.xueqiu.com/v5/stock/chart/kline.json'
    timestamp = str(int(datetime.datetime.now().timestamp() * 1000 // 1))
    indicator = 'kline,ma,macd,kdj,boll,rsi,wr,bias,cci,psy,pe,pb,ps,pcf,market_capital,agt,ggt,balance'
    params = {
        'symbol': code,
        'begin': timestamp,
        'period': 'day',
        'type': 'before',
        'count': '-' + str(days),
        'indicator': indicator
    }
    return session.get(url, params=params, headers=headers, cookies=cookies)

def calculateBiKiller(code, count):
    if code in blackListSet:
        raise Exception('代码在黑名单中')
    result = getHistoryData(code, count).result()
    stringResponse = result.content.decode()

    return resolveData(json.loads(stringResponse))

# 校验返回数据的时间序列是否正确
def checkTimeSequence(itemList, timestampPosition):
    for index, item in enumerate(itemList):
        if index > 0 and index < len(itemList):
            current = itemList[index]
            former = itemList[index - 1]
            if current[timestampPosition] < former[timestampPosition]:
                return False
    return True

def getCollection(itemList, index):
    result = []
    for item in itemList:
        result.append(item[index])
    return result

def formatDate(timestamp):
    return datetime.datetime.fromtimestamp(timestamp // 1000).strftime(timeformat)

def trim(string):
    return str.strip(string)

def resolveData(raw):
    print(raw)
    data = raw['data']
    code = data['symbol']
    column = data['column']
    itemList = data['item']
    totalLength = len(itemList)
    if totalLength == 0:
        raise Exception('无数据')

    if checkTimeSequence(itemList, column.index('timestamp')) is not True:
        raise Exception('序列错误')

    closeList = getCollection(itemList, column.index('close'))
    jidazhi = []
    for index, stock in enumerate(closeList):
        if index > 0 and index < len(closeList) - 1:
            former = closeList[index - 1]
            current = closeList[index]
            later = closeList[index + 1]
            if current >= former and current >= later:
                jidazhi.append(current)

    jixiaozhi = []
    for index, stock in enumerate(closeList):
        if index > 0 and index < len(closeList) - 1:
            former = closeList[index - 1]
            current = closeList[index]
            later = closeList[index + 1]
            if current <= former and current <= later:
                jixiaozhi.append(current)

    lastItem = itemList[-1]
    lastEndPrice = lastItem[column.index('close')]
    maxAverage = np.mean(jidazhi)
    minAverage = np.mean(jixiaozhi)
    totalAverage = np.mean([maxAverage, minAverage])
    diffPercent = (lastEndPrice - totalAverage) / totalAverage * 100

    return {
        "code": code,
        "last": lastEndPrice,
        "maxAverage": maxAverage,
        "minAverage": minAverage,
        "diffPercent": diffPercent,
        "avg": totalAverage,
        "count": totalLength,
        "column": column,
        "data": itemList,
        "updateDate": int(datetime.datetime.now().timestamp() * 1000 // 1)
    }

def loadShanghaiStock():
    return loadJsonFile('../assets/shanghai.json')

def loadShenzhenStock():
    return loadJsonFile('../assets/shenzhen.json')

def getTotalStockList():
    result = []
    for stock in list(loadShanghaiStock()):
        result.append({
            "name": trim(stock["name"]),
            "code": 'SH' + trim(stock['code'])
        })

    for stock in list(loadShenzhenStock()):
        result.append({
            "name": trim(stock["name"]),
            "code": 'SZ' + trim(stock['code'])
        })
    return result

async def updateStockDocument(stock):
    try:
        item = calculateBiKiller(stock.get('code'), 420)
        historyDocument.update({"code": item.get("code")}, item, True)
    except:
        print('err')
        pass
    finally:
        print('done')
        pass


loop = asyncio.get_event_loop()

def synchronizeStockData():
    stockList = getTotalStockList()
    for stock in list(stockList):
        loop.run_until_complete(updateStockDocument(stock))


def synchronizeStockBase():
    refreshToken()
    stockList = getTotalStockList()
    totalLength = len(stockList)
    current = 0
    resultList = []
    for stock in list(stockList):
        try:
            result = getStockBase(stock.get('code')).get('data').get('quote')
            resultList.append(result)
        except:
            pass
        finally:
            current += 1
            print('{current}/{total}'.format(current=current, total=totalLength))
    for item in list(resultList):
        if item is not None:
            database.base.update({ "code": item.get('symbol')}, item, True)

if __name__ == '__main__':
    synchronizeStockData()
    # itchat.auto_login(hotReload=True)
    # itchat.run(True)
