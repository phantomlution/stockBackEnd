'''
    提取汇通网的数据
'''
from src.service.HtmlService import get_response
from bs4 import BeautifulSoup
from src.utils.extractor import Extractor
import json

bank_list = [
    { "key": 'FED', "name": '美联储' },
    { "key": "ECB", "name": "欧洲央行" },
    { "key": "BOE", "name": "英国央行" },
    { "key": "BOJ", "name": "日本央行" },
    { "key": "BOC", "name": "加拿大央行" },
    { "key": "RBA", "name": "澳洲联储" },
    { "key": "RBNZ", "name": "新西兰联储" },
    { "key": "SNB", "name": "瑞士央行" }
]


def get_central_bank_schedule(model):
    key = model['key']
    url = 'https://bank.fx678.com/' + str(key)
    raw_html = get_response(url)

    html = BeautifulSoup(raw_html, 'html.parser')
    body = html.select('.schedule')[0]
    content_doc = body.select('table')[0]
    extractor = Extractor(content_doc)
    extractor.parse()
    parsed_result = extractor.return_list()

    event_list = []
    for rowIndex, row in enumerate(parsed_result):
        if rowIndex > 0:
            for columnIndex, column in enumerate(row):
                if columnIndex > 0 and len(column) > 0:
                    year = row[0].split('年')[0]
                    month = column.split('月')[0]
                    day = column.split('月')[1].split('日')[0]
                    date = str(year) + '-' + str(month) + '-' + str(day)
                    event_list.append({
                        "date": date,
                        'event': str.strip(parsed_result[0][columnIndex])
                    })

    # 按照日期合并事件
    event_map = {}
    for event in event_list:
        date = event['date']
        if date not in event_map:
            event_map[date] = []
        event_map[date].append(event['event'])

    result = []
    for key in event_map:
        result.append({
            "date": key,
            "event": ','.join(event_map[key])
        })

    return result


class FxService:

    # 提取各国央行的会议事件节点
    @staticmethod
    def get_central_bank_schedule_list():
        result = []

        for bank in bank_list:
            result.append({
                "name": bank['name'],
                'code': bank['key'],
                'list': get_central_bank_schedule(bank)
            })

        return result

    @staticmethod
    def get_quote(item):
        item = str.upper(item)
        url = 'https://api-q.fx678.com/getQuote.php'

        params = {
            "exchName": 'WGJS',
            "symbol": item,
            'st': '0.8183158721255273'
        }

        headers = {
            'Host': 'api-q.fx678.com',
            'Origin': 'https://quote.fx678.com',
            'Referer': 'https://quote.fx678.com/HQApi/XAU'
        }
        raw_response = get_response(url, params=params, headers=headers)
        result = json.loads(raw_response)

        if result['s'] != 'ok':
            raise Exception('获取{}失败'.format(item))

        return {
            "open": float(result['o'][0]),
            'current': float(result['c'][0]),
            'pre_close': float(result['p'][0])
        }


if __name__ == '__main__':
    result = FxService.get_quote('xau')
    print(result)