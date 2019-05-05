import datetime
import numpy as np
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import itchat
from src.service.stockService import StockService
from src.utils.sessions import FuturesSession

FILE_HELPER = 'filehelper'

null = None
timeformat = '%Y-%m-%d'

SHOW_DETAIL = False

client = StockService.getMongoInstance()
database = client.stock
historyDocument = database.history

session = FuturesSession(max_workers=50)

fetch_cookie_url = 'https://xueqiu.com/S/SZ000007'

def loadToken():
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(chrome_options=options)
    driver.get(fetch_cookie_url)
    cookies = driver.get_cookies()
    cookie_fields_set = set([
        'xq_a_token',
        'xq_a_token.sig',
        'xq_r_token',
        'xq_r_token.sig'
    ])
    result = {}
    for cookie in cookies:
        cookie_name = cookie['name']
        cookie_value = cookie['value']
        if cookie_name in cookie_fields_set:
            result[cookie_name] = cookie_value
    driver.quit()
    return result

cookies = {}

# make sure your token is valid
def refreshToken():
    cookies = loadToken()

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
    data = raw['data']
    code = data['symbol']
    column = data['column']
    itemList = data['item']
    totalLength = len(itemList)
    if totalLength == 0:
        raise Exception('无数据')
    #if len(itemList) < MIN_COUNT:
    #    raise Exception('数据不足' + str(MIN_COUNT))
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

    dateList = getCollection(itemList, column.index('timestamp'))

    lastItem = itemList[-1]
    lastEndPrice = lastItem[column.index('close')]
    maxAverage = np.mean(jidazhi)
    minAverage = np.mean(jixiaozhi)
    totalAverage = np.mean([maxAverage, minAverage])
    diffPercent = (lastEndPrice - totalAverage) / totalAverage * 100

    brief = ''
    brief += '{start} 至 {end}\n({count}个数据)'.format(count=totalLength, start=formatDate(dateList[0]), end=formatDate(dateList[-1]))
    brief += '\n\n代码：{code}'.format(code=code)
    brief += '\n\n{date}\n收盘：{price}'.format(date=formatDate(lastItem[column.index('timestamp')]), price=numberFormat(lastEndPrice))
    brief += '\n偏移量' + ('+' if diffPercent > 0 else '') + numberFormat(diffPercent) + '%'
    brief += '\n估：' + numberFormat(minAverage * 0.8)
    brief += '\n\n极大值个数：{count}，极大均值：{avg}，最大值：{max}'.format(count=len(jidazhi), avg=numberFormat(maxAverage), max=numberFormat(np.max(jidazhi)))
    brief += '\n\n极小值个数：{count}，极小均值：{avg}，最小值：{min}'.format(count=len(jixiaozhi), avg=numberFormat(minAverage), min=numberFormat(np.min(jixiaozhi)))

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
        "updateDate": int(datetime.datetime.now().timestamp() * 1000 // 1),
        "brief": brief
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

def synchronizeStockData():
    stockList = getTotalStockList()
    totalLength = len(stockList)
    current = 0
    # stockList = [stockList[0]]
    resultList = []
    for stock in list(stockList):
        # result = calculateBiKiller(stock.get('code'), 420)
        try:
            item = calculateBiKiller(stock.get('code'), 420)
            print(item)
            historyDocument.update({ "code": item.get("code") }, item, True)
        except:
            print('err')
            pass
        finally:
            current += 1
            print('{current}/{total}'.format(current=current, total=totalLength))

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
    synchronizeStockBase()
    #result = getStockBase("SZ000007")
    # print(result)
    #synchronizeStockData()
    # itchat.auto_login(hotReload=True)
    # itchat.run(True)
