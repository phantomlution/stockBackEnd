from datetime import date, datetime

def getCurrent():
    return datetime.now()

def getTimestamp(dateObj):
    return int(dateObj.timestamp() * 1000)

def getCurrentTimestamp():
    return getTimestamp(getCurrent())

def getDaysFrom2000(date1):
    d0 = date(2000, 1, 1)

    delta = date1 - d0
    return delta.days

