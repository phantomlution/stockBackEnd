import requests
from bs4 import BeautifulSoup
from src.utils.extractor import Extractor

def getHtml(date):
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
    }

    url = 'https://rl.fx678.com/date/' + str(date) + '.html'
    response = requests.get(url, headers=headers)
    return response.text


def extractData(date):
    raw_html = getHtml(date)

    # 修正部分html
    for rate in range(4):
        raw_html = raw_html.replace('<img src="/Public/images/star_' + str(rate) + '.png">', '<span>' + str(rate) + '</span>')

    html = BeautifulSoup(raw_html, 'html.parser')
    body = html.select('.calendar_content > *')
    table_item_list = []
    for content in body:

        if 'sq_logo' in content['class']:
            raw_text = content.select_one('*').text
            text = raw_text.replace('\n', ' ').split(' ')[0].split('(')[0]
            table_item_list.append({
                "name": text,
                "data": []
            })
        elif len(table_item_list) > 0:
            if content.name == 'table':
                table_element = [content]
            else:
                table_element = content.select('table')
                if len(table_element) == 0:
                    continue

            if len(table_element) > 0:
                for table_doc in table_element:
                    extractor = Extractor(table_doc)
                    extractor.parse()
                    result = extractor.return_list()
                    for rowIndex, row in enumerate(result):
                        for columnIndex, column in enumerate(row):
                            row[columnIndex] = str.strip(row[columnIndex].replace('\n', ''))

                        # 去重
                        if rowIndex > 0 and row == result[rowIndex - 1]:
                            continue
                        
                        # 归并数据
                        table_item_list[-1]["data"].append(row)
                     
    # 调整数据                    
    for table in table_item_list:
        table_data = table['data']
        print(table_data)
        for rowIndex, row in enumerate(table_data):
            for columnIndex, column in enumerate(row):
                    # 调整部分数据标记
                    if columnIndex < len(table_data[0]) and table_data[0][columnIndex] == '重要性':
                        if row[columnIndex] == '高':
                            row[columnIndex] = '3'
                        elif row[columnIndex] == '中':
                            row[columnIndex] = '2'
                        elif row[columnIndex] == '低':
                            row[columnIndex] = '1'

    return table_item_list
