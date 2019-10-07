'''
    用于提取一次性数据
'''
import json
from src.service.HtmlService import get_response
from src.utils.extractor import Extractor
from bs4 import BeautifulSoup
from src.service.StockService import StockService
import re
client = StockService.getMongoInstance()
huitong_document = client.stock.huitong


def load_chinese_foreign_exchange():
    url = 'http://www.safe.gov.cn/safe/2019/0211/11348.html'
    raw_html = get_response(url)
    html = BeautifulSoup(raw_html, 'html.parser')
    content_doc = html.select_one('table')
    extractor = Extractor(content_doc)
    extractor.parse()
    return_list = extractor.return_list()
    result = []
    for month in range(12):
        index = 2 * month + 1
        result.append({
            "date": return_list[2][index].replace('.', '-') + '-06',
            "value": str.strip(return_list[5][index])
        })

    return result

# 加载汇通网目前提供的图表信息
def load_fx_chart_index():
    url = 'https://rl.fx678.com/getcategory.html'
    country_list = [
        "美元", "欧元", '英镑', "澳元", "人民币"
    ]

    for country in country_list:
        params = {
            "country": country
        }
        index_list = get_response(url, params=params)
        for index_item in json.loads(index_list):
            index_item['country'] = country
            huitong_document.update({ "IDX_ID": index_item['IDX_ID']}, index_item, True)


# 读取美国财政部公布的外国持有美债数量
def load_american_treasury_securities():
    url = 'https://ticdata.treasury.gov/Publish/mfh.txt'
    raw_data = get_response(url)
    start_offset = 'PERIOD'
    country_header = 'Country'
    separator_offset = '-----'
    # print(raw_data)
    # 提取标题
    header_start = raw_data.index(start_offset)
    header_end = raw_data.index(separator_offset)
    body_start = raw_data.rindex(separator_offset)
    body_end = raw_data.index('All Other')

    pre_header = raw_data[header_start + len(start_offset):header_end]
    if country_header not in pre_header:
        raise Exception('header 数据异常')

    pre_header = str.strip(pre_header)

    header = str.strip(pre_header)
    header_item = header.replace(country_header, '').split('\r\n')
    month = re.sub(r'\s+', ' ', str.strip(header_item[0])).split(' ')
    year = re.sub(r'\s+', ' ', str.strip(header_item[1])).split(' ')

    month_map = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    sheet_header = ['Country']
    for idx, month_item in enumerate(month):
        month_index = month_map.index(month_item)
        if month_index == -1:
            raise Exception('月份异常')
        sheet_header.append('{}-{}{}'.format(year[idx], '0' if month_index + 1 < 10 else '', str(month_index + 1)))

    sheet = [sheet_header]

    # 提取内容
    body = raw_data[body_start + len(separator_offset):body_end]
    for body_item in body.split('\r\n'):
        if len(body_item) == 0:
            continue

        country_data = re.sub(r'\s{2,}', '  ', body_item).split('  ')
        sheet.append(country_data)

    print(sheet)

load_american_treasury_securities()