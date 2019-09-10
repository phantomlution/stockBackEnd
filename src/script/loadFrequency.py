from src.utils.keywordFrequent import search
from datetime import datetime, timedelta, date
from src.utils.date import getDaysFrom2000
from src.utils.db import MySQL
from src.service.stockService import StockService

mysql = MySQL()
now = datetime.now()

baseDiff = getDaysFrom2000(now.date())

duplicateSql = 'select `id` from hot_index where `code`=%s and `days`=%s'

# 不自动过滤状态
enableSkipSetting = False

# 加载关键词热度
def loadIndex(code, key, days):
    result = search(key, days)
    for index, val in enumerate(result):
        if val == '':
            val = 0
        daysDiff = baseDiff - days + index
        model = {
            "code": code,
            "days": daysDiff,
            "date": date(2000, 1, 1) + timedelta(days=daysDiff),
            "index": val
        }

        item = mysql.find(duplicateSql, (code, daysDiff))
        if item is None:
            mysql.execute('insert into `hot_index`(`code`, `days`, `date`, `index`) values(%s, %s, %s, %s)',
                      (model["code"], model["days"], model["date"], model["index"]))


result = StockService.get_stock_list()

for item in result:
    try:
        loadIndex(item['code'], item['name'], 1)
    except(TypeError):
        if enableSkipSetting:
            mysql.execute('update stock set `skip`=%s where code=%s', (1, item["code"]))
