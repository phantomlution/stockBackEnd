'''
    获取各国央行的数据
'''

import requests
from bs4 import BeautifulSoup
from src.utils.extractor import Extractor


def getHtml(key):
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
    }

    url = 'https://bank.fx678.com/' + str(key)
    response = requests.get(url, headers=headers)
    return response.text


def extractData(model):
    key = model['key']
    raw_html = getHtml(key)

    html = BeautifulSoup(raw_html, 'html.parser')
    body = html.select('.schedule')[0]
    content_doc = body.select('table')[0]
    extractor = Extractor(content_doc)
    extractor.parse()
    result = extractor.return_list()

    date_set = set()
    for rowIndex, row in enumerate(result):
        if rowIndex > 0:
            for columnIndex, column in enumerate(row):
                if columnIndex > 0 and len(column) > 0:
                    year = row[0].split('年')[0]
                    month = column.split('月')[0]
                    day = column.split('月')[1].split('日')[0]
                    date = str(year) + '-' + str(month) + '-' + str(day)
                    date_set.add(date)

    return list(date_set)

def extractAllCentualBank():
    bank_list = [
        {
            "key": 'FED',
            "name": '美联储'
        },
        {
            "key": "ECB",
            "name": "欧洲央行"
        },
        {
            "key": "BOE",
            "name": "英国央行"
        },
        {
            "key": "BOJ",
            "name": "日本央行"
        },
        {
            "key": "BOC",
            "name": "加拿大央行"
        },
        {
            "key": "RBA",
            "name": "澳洲联储"
        },
        {
            "key": "RBNZ",
            "name": "新西兰联储"
        },
        {
            "key": "SNB",
            "name": "瑞士央行"
        }
    ]

    date_map = {}

    for bank in bank_list:
        date_list = extractData(bank)
        for date in date_list:
            if date not in date_map:
                date_map[date] = []

            date_map_item_list = date_map[date]
            date_map_item_list.append(bank['name'])

    result = []
    for date in date_map.keys():
        result.append({
            "date": date,
            "bankList": date_map[date]
        })

    return {
        "bankList": bank_list,
        "data": result
    }


extractAllCentualBank()

