from datetime import date, datetime


time_format = '%Y-%m-%d'

def getCurrent():
    return datetime.now()


def getTimestamp(dateObj):
    return int(dateObj.timestamp() * 1000)


def getCurrentTimestamp():
    return getTimestamp(getCurrent())


def format_timestamp(timestamp, format_rule=time_format):
    return datetime.fromtimestamp(timestamp // 1000).strftime(format_rule)


def getDaysFrom2000(date1):
    d0 = date(2000, 1, 1)

    delta = date1 - d0
    return delta.days

