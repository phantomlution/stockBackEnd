import datetime
import json
import time
from src.service.stockService import StockService
from src.utils.sessions import FuturesSession
import asyncio
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

def numberFormat(num):
    return '%.2f' % num


def getStockBase(code):
    url = 'https://stock.xueqiu.com/v5/stock/quote.json?symbol=' + str(code)

    return json.loads(session.get(url, headers=headers, cookies=cookies).result().content.decode())



def formatDate(timestamp):
    return datetime.datetime.fromtimestamp(timestamp // 1000).strftime(timeformat)

def trim(string):
    return str.strip(string)

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

def initDatabase():
    # 初始化数据库
    # 1. 同步基础信息
    synchronizeStockBase()
    # 2. 同步公司简介
    synchronizeStockCompanyIntroduction()

def getScheduledTaskTime(start, minutesOffset):
    date = start + datetime.timedelta(minutes=minutesOffset)
    return datetime.datetime.strftime(date, '%H:%M')


def runEveryDayRoutine():
    now = datetime.datetime.now()
    # 0. 同步当日资金
    # schedule.every().day.at(getScheduledTaskTime(now, 1)).do(synchronizeCapitalDataTask).tag('daily-tasks')
    # 1. 同步股票数据
    # schedule.every().day.at(getScheduledTaskTime(now, 2)).do(synchronizeStockData).tag('daily-tasks')
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


