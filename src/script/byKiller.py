import datetime
import numpy as np
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from src.service.stockService import StockService
from src.utils.sessions import FuturesSession
import asyncio
from src.utils.date import getCurrentTimestamp
import schedule

FILE_HELPER = 'filehelper'

null = None
timeformat = '%Y-%m-%d'

SHOW_DETAIL = False

client = StockService.getMongoInstance()
database = client.stock
historyDocument = database.history
baseDocument = database.base
noticeDocument = database.notice
themeDocument = database.theme
capitalFlowDocument = database.capitalFlow
hotMoneyDocument = database.hotMoney

session = FuturesSession(max_workers=1)

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

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Origin': 'https://xueqiu.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
}

def loadJsonFile(filePath):
    with open(filePath) as json_file:
        data = json.load(json_file)
        return data

def numberFormat(num):
    return '%.2f' % num


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
    if 'symbol' not in data:
        raise Exception('数据不存在')
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

finish_count = 0
totalStockLength = 0

async def updateStockDocument(stock):
    time.sleep(0.3)
    global finish_count
    global totalStockLength
    try:
        item = calculateBiKiller(stock.get('code'), 420)
        historyDocument.update({"code": item.get("code")}, item, True)
    except Exception as e:
        print(stock)
        print(e)
        pass
    finally:
        finish_count += 1
        print('done: {finish_count}/{totalStockLength},{progress}%'.format(finish_count=finish_count,
                                                                           totalStockLength=totalStockLength,
                                                                           progress=finish_count * 100 // totalStockLength))

        pass

async def updateDocumentCompanyIntrodution(code):
    global finish_count
    global totalStockLength
    try:
        result = loadStockIntroduction(code)
        baseDocument.update({"symbol": code}, {"$set": {"company": result}})
    except Exception as e:
        print(e)
        pass
    finally:
        finish_count += 1
        print('done: {finish_count}/{totalStockLength},{progress}%'.format(finish_count=finish_count,
                                                                           totalStockLength=totalStockLength,
                                                                           progress=finish_count * 100 // totalStockLength))

        pass


loop = asyncio.get_event_loop()

def synchronizeStockData():
    global totalStockLength
    stockList = getTotalStockList()
    totalStockLength = len(stockList)
    for stock in list(stockList):
        loop.run_until_complete(updateStockDocument(stock))

def synchronizeStockCompanyIntroduction():
    global totalStockLength
    stockList = getTotalStockList()
    totalStockLength = len(stockList)
    for stock in list(stockList):
        code = stock.get('code')
        loop.run_until_complete(updateDocumentCompanyIntrodution(code))


def synchronizeStockBase():
    refreshToken()
    stockList = getTotalStockList()
    totalLength = len(stockList)
    current = 0
    for stock in list(stockList):
        time.sleep(0.3)
        try:
            item = getStockBase(stock.get('code')).get('data').get('quote')
            if item is not None:
                baseDocument.update({"code": item.get('symbol')}, item, True)
        except Exception as e:
            print(e)
            pass
        finally:
            current += 1
            print('{current}/{total}'.format(current=current, total=totalLength))

def removeOldDocuments():
    database.history.drop()


def loadStockIntroduction(code):
    url = 'https://stock.xueqiu.com/v5/stock/f10/cn/company.json?symbol=' + str(code)
    response = json.loads(session.get(url, headers=headers, cookies=cookies).result().content.decode())
    return response['data']['company']


def synchronizeAllNotice():
    global totalStockLength
    stockList = getTotalStockList()
    totalStockLength = len(stockList)
    for stock in list(stockList):
        code = stock.get('code')[2:]
        loop.run_until_complete(asynchrinizeLoadStockNotice(code))


def loadStockNotice(code):
    url = "http://data.eastmoney.com/notices/getdata.ashx"
    params = {
        "StockCode": code,
        "CodeType": 1,
        "PageIndex": 1,
        "PageSize": 50,
        "jsObj": "dHBlUEvg",
        "SecNodeType": 0,
        "FirstNodeType": 0
    }
    content = session.get(url, params=params).result().content.decode('gbk')
    content_json = trim(content[content.find('=') + 1:-1])
    return content_json

async def asynchrinizeLoadStockNotice(code):
    global finish_count
    global totalStockLength
    time.sleep(0.3)
    try:
        item = loadStockNotice(code)
        if item is not None:
            item = json.loads(item)
            if len(item['data']) > 0:
                item['code'] = code
                noticeDocument.update({"code": item.get('code')}, item, True)
    except Exception as e:
        print(e)
        pass
    finally:
        finish_count += 1
        print('done: {finish_count}/{totalStockLength},{progress}%'.format(finish_count=finish_count,
                                                                           totalStockLength=totalStockLength,
                                                                           progress=finish_count * 100 // totalStockLength))
        pass

def loadStockTheme(code):
    url = "http://f10.eastmoney.com/CoreConception/CoreConceptionAjax"
    params = {
        "code": code
    }
    content = session.get(url, params=params).result().content
    response = json.loads(content)
    if 'hxtc'in response:
        if len(response['hxtc']) > 0:
            return response['hxtc'][0]['ydnr'].split(' ')

    return null

async def asynchrinizeLoadStockTheme(code):
    global finish_count
    global totalStockLength
    time.sleep(0.3)
    try:
        theme = loadStockTheme(code)
        if theme is not None:
            model = {
                "code": code,
                "theme": theme
            }
            themeDocument.update({"code": model.get('code')}, model, True)
    except Exception as e:
        print(e)
        pass
    finally:
        finish_count += 1
        print('done: {finish_count}/{totalStockLength},{progress}%'.format(finish_count=finish_count,
                                                                           totalStockLength=totalStockLength,
                                                                           progress=finish_count * 100 // totalStockLength))
        pass

def synchronizeStockTheme():
    global totalStockLength
    stockList = getTotalStockList()
    totalStockLength = len(stockList)
    for stock in list(stockList):
        code = stock.get('code')
        loop.run_until_complete(asynchrinizeLoadStockTheme(code))

def getFarmProductIndex(code):
    url = "http://www.chinaap.com/chinaapindex/index/getBrokenLine"
    params = {
        "goodsId": code
    }
    content = session.post(url, data=params).result().content
    result = json.loads(content)
    return result

def synchronizeCapitalFlow():
    data = getRealTimeCapitalFlow()
    if 'ya' not in data:
        raise Exception('数据异常')
    # [0] 主力净流入
    # [1] 超大单净流入
    # [2] 大单净流入
    # [3] 中单净流入
    # [4] 小单净流入
    ya = data['ya']
    lastYaItem = ya[-1]
    if lastYaItem == ',,,,':
        raise Exception('数据不完整，请于15点后同步')

    model = {
        "date": formatDate(getCurrentTimestamp()),
        "data": data
    }

    capitalFlowDocument.update({ "date": model["date"] }, model, True)
    print('synchronize capital flow success')



def getRealTimeCapitalFlow():
    url = 'http://ff.eastmoney.com/EM_CapitalFlowInterface/api/js'
    params = {
        "id": "ls",
        "type": "ff",
        "check": "MLBMS",
        "cb": "var aff_data =",
        "js": "{(x)}",
        "rtntype": 3,
        "date": "2019-09-11",
        "acces_token": "1942f5da9b46b069953c873404aad4b5",
        "_": getCurrentTimestamp()
    }

    content = session.get(url, params=params).result().content
    content = str(content)
    content_json = trim(content[content.find('=') + 1:-1])
    return json.loads(content_json)

def synchronizeHotMoney():
    raw = getHotMoneyData()
    if 'data' not in raw:
        raise Exception('数据异常')
    raw_data = raw['data']
    response_date = raw_data['n2sDate']
    current_date = time.strftime('%m-%d')
    if response_date != current_date:
        raise Exception('没有当天的数据')

    '''
        s2n: 北向资金
            0. 时间点
            1. 沪股通流入金额
            2. 沪股通余额
            3. 深股通流入金额
            4. 深股通余额
    
        n2s: 南向资金
            0. 时间点
            1. 港股通(沪)流入金额
            2. 港股通(沪)余额
            3. 港股通(深)流入金额
            4. 港股通(深)余额
    '''


    raw_data['date'] = time.strftime('%Y-%m-%d')

    hotMoneyDocument.update({"date": raw_data["date"]}, raw_data, True)
    print('synchronize hot money success')


def getHotMoneyData():
    url = 'http://push2.eastmoney.com/api/qt/kamt.rtmin/get'
    current = getCurrentTimestamp()
    params = {
        "fields1": "f1,f2,f3,f4",
        "fields2": "f51,f52,f53,f54,f55,f56",
        "cb": "jQuery18304445605268991899_" + str(current),
        "_": current
    }

    headers = {
        "Referer": "http://data.eastmoney.com/hsgt/index.html",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
    }

    content = session.get(url, params=params, headers=headers).result().content
    content = str(content)[len(params['cb']) + 3:-3]
    return json.loads(content)

def synchronizeCapitalData():
    # 同步大盘资金
    synchronizeCapitalFlow()
    # 同步南北向资金
    synchronizeHotMoney()

def initDatabase():
    # 初始化数据库
    # 1. 同步基础信息
    synchronizeStockBase()
    # 2. 同步公司简介
    synchronizeStockCompanyIntroduction()

def getScheduledTaskTime(start, minutesOffset):
    date = start + datetime.timedelta(minutes=minutesOffset)
    return datetime.datetime.strftime(date, '%H:%M')

def synchronizeCapitalDataTask():
    try:
        synchronizeCapitalData()
    except Exception as e:
        print(e)

def runEveryDayRoutine():
    now = datetime.datetime.now()
    # 0. 同步当日资金
    schedule.every().day.at(getScheduledTaskTime(now, 1)).do(synchronizeCapitalDataTask).tag('daily-tasks')
    # 1. 同步股票数据
    schedule.every().day.at(getScheduledTaskTime(now, 2)).do(synchronizeStockData).tag('daily-tasks')
    # 2. 同步公告
    schedule.every().day.at(getScheduledTaskTime(now, 30)).do(synchronizeAllNotice).tag('daily-tasks')
    # 3. 同步主题
    schedule.every().day.at(getScheduledTaskTime(now, 60)).do(synchronizeStockTheme).tag('daily-tasks')

def job():
    print("I'm working...")



if __name__ == '__main__':
    # 每日同步任务
    runEveryDayRoutine()
    while True:
        schedule.run_pending()


