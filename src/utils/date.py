from datetime import date, datetime, timedelta


time_format = '%Y-%m-%d'

full_time_format = time_format + ' %H:%M:%S'


def getCurrent():
    return datetime.now()


def get_current_date_str():
    return getCurrent().strftime(time_format)


def get_current_datetime_str():
    return getCurrent().strftime(full_time_format)


def date_str_to_timestamp(date_str, format_rule=time_format):
    return date_obj_to_timestamp(datetime.strptime(date_str, format_rule))


def date_obj_to_timestamp(date_obj):
    return int(date_obj.timestamp() * 1000)


def getCurrentTimestamp():
    return date_obj_to_timestamp(getCurrent())


def format_timestamp(timestamp, format_rule=time_format):
    return datetime.fromtimestamp(timestamp // 1000).strftime(format_rule)


def getDaysFrom2000(date1):
    d0 = date(2000, 1, 1)

    delta = date1 - d0
    return delta.days


# 按照天数的长度，将日期拆分成多个子区间
def get_split_range(start, end, duration):
    result = []
    start_date = datetime.strptime(start, time_format)
    end_date = datetime.strptime(end, time_format)
    while start_date + timedelta(days=duration) <= end_date:
        result.append({
            "start": start_date.strftime(time_format),
            "end": (start_date + timedelta(days=duration - 1)).strftime(time_format)
        })
        start_date = start_date + timedelta(days=duration)
    result.append({
        "start": start_date.strftime(time_format),
        "end": end_date.strftime(time_format)
    })

    return result
