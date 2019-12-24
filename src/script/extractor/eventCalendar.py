'''
    提取数据源中的财经事件
'''
from bs4 import BeautifulSoup
from src.utils.extractor import Extractor
from src.service.HtmlService import get_response
from src.utils.date import getCurrentTimestamp


def get_raw_table_data(date):
    date = date.replace('-', '')
    url = 'https://rl.fx678.com/date/' + str(date) + '.html'
    raw_html = get_response(url)

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
                    element_attrs = table_doc.attrs
                    # 跳过更多数据
                    if 'id' in element_attrs and element_attrs['id'] == 'moreData' and 'cjsj_tab' in element_attrs['class']:
                        continue
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


def get_field_column_index(header, name):
    return list.index(header, name)


def parse_financial_data(financial_raw_data):
    table_header = financial_raw_data[0]
    table_data = financial_raw_data[1:]

    time_index = get_field_column_index(table_header, '时间')
    zone_index = get_field_column_index(table_header, '区域')
    indicator_index = get_field_column_index(table_header, '指标')

    result = []
    for item in table_data:
        if len(item[indicator_index]) == 0:
            continue
        model = {
            "time": item[time_index],
            "area": item[zone_index],
            "name": item[indicator_index]
        }
        result.append(model)

    return result


def parse_financial_event(financial_raw_event):
    table_header = financial_raw_event[0]
    if table_header[0] == '暂无财经大事':
        return []

    table_data = financial_raw_event[1:]

    time_index = get_field_column_index(table_header, '时间')
    country_index = get_field_column_index(table_header, '国家地区')
    zone_index = get_field_column_index(table_header, '地点')
    event_index = get_field_column_index(table_header, '事件')

    result = []

    for item in table_data:
        if len(item[event_index]) == 0:
            continue
        model = {
            "time": item[time_index],
            "country": item[country_index],
            "area": item[zone_index],
            "name": item[event_index]
        }
        result.append(model)
    return result


def get_event_calendar_item(date):
    table_raw_list = get_raw_table_data(date)
    financial_data = list(filter(lambda item: item['name'] == '财经数据', table_raw_list))
    if len(financial_data) == 0:
        raise Exception('找不到财经数据')
    financial_event = list(filter(lambda item: item['name'] == '财经大事件', table_raw_list))
    if len(financial_event) == 0:
        raise Exception('找不到财经大事件')

    financial_data_model = parse_financial_data(financial_data[0]['data'])
    financial_event_model = parse_financial_event(financial_event[0]['data'])

    result = []

    for item in financial_data_model:
        item['date'] = date
        item['type'] = 'financial_data'

        result.append(item)

    for item in financial_event_model:
        item['date'] = date
        item['type'] = 'financial_event'
        result.append(item)

    for item in result:
        # 唯一性
        item['key'] = date + '_' + item['name']
        item['created_date'] = getCurrentTimestamp()

    return result


print(get_event_calendar_item('2019-12-24'))
