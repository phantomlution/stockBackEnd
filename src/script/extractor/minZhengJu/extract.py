'''
    提取民政局信息

    数据格式：
        年_季度 + 数据
'''
from src.service.HtmlService import get_response, get_absolute_url_path, get_html_variable, extract_table
from bs4 import BeautifulSoup
from src.service.StockService import StockService

client = StockService.getMongoInstance()
min_zheng_ju_document = client.stock.min_zheng_ju
source_url = 'http://www.mca.gov.cn/article/sj/tjjb/sjsj/?'


def get_total_page():
    url = source_url
    raw_html = get_response(url)
    total_page = get_html_variable(raw_html, 'totalpage', variable_define=False)
    if total_page is None:
        raise Exception('摘不到页数')
    return total_page


def get_source_list(page):
    if page == 1:
        page_str = ''
    else:
        page_str = str(page)
    url = source_url + page_str
    raw_html = get_response(url)
    html = BeautifulSoup(raw_html, 'html.parser')
    table = html.select_one('table')

    result = []
    for row in table.select('tr'):
        item = row.select_one('a')
        if item is None:
            continue
        file_name = item.text
        href = item['href']

        target_string = file_name.split('季度')[0]
        split_string = target_string.split('年')
        year_string = split_string[0]
        quarter_string = split_string[1]
        if quarter_string == '四':
            quarter_string = '4'
        if quarter_string == '三':
            quarter_string = '3'
        if quarter_string == '二':
            quarter_string = '2'
        if quarter_string == '一':
            quarter_string = '1'

        if len(year_string) != 4:
            raise Exception('年份异常')
        elif quarter_string not in ['1', '2', '3', '4']:
            raise Exception('月份异常')

        result.append({
            "year": year_string,
            "quarter": quarter_string,
            "url": get_absolute_url_path(url, href)
        })

    return result


def extract_data(model):
    target_url = model['url']
    final_url = get_final_url(target_url)
    model['final_url'] = final_url
    year = model['year']
    print('{}年{}季度'.format(year, model['quarter']))

    raw_html = get_response(final_url)
    html = BeautifulSoup(raw_html, 'html.parser')
    item_list = extract_table(html.select_one('table'))

    result = {
        "rows": []
    }

    model['data'] = result

    for item in item_list:
        first_column = str.strip(item[0])
        if (year + '年') in first_column or len(first_column) == 0 or first_column == '本部级':
            continue
        elif first_column == '单位':
            units = []
            for unit_item in item:
                units.append(str.strip(unit_item))
            result['units'] = units
        elif first_column == '地区':
            headers = []
            for header_item in item:
                headers.append(str.strip(header_item))
            result['headers'] = headers
        else:
            result['rows'].append(item)

    return result


def get_final_url(url):
    raw_html = get_response(url)
    html = BeautifulSoup(raw_html, 'html.parser')
    body = html.select_one('body')
    real_url = get_html_variable(body.text, 'window.location.href', variable_define=False)

    return get_absolute_url_path(url, real_url)


def run():
    total_page = get_total_page()
    for page in range(int(total_page)):
        source_list = get_source_list(page + 1)
        for model in source_list:
            model['key'] = model['year'] + '_' + model['quarter']
            if min_zheng_ju_document.find_one({ "key": model['key']}) is None:
                extract_data(model)
                min_zheng_ju_document.update({ "key": model['key']}, model, True)


# 统计数据, 统计结婚人数，离婚人数，部分数据有单位，可能需要转化
def do_statistics(start, end, quarter_list, target_row, field_list):

    if len(quarter_list) == 0:
        raise Exception('请选择季度')
    elif len(quarter_list) == 1:
        quarter_str = quarter_list[0]
    else:
        quarter_str = quarter_list[0] + '-' + quarter_list[-1]

    for year in range(start, end + 1):
        year_item_list = min_zheng_ju_document.find({ "year": str(year), "quarter": { "$in": quarter_list } })
        model = {
            "title": str(year) + '年' + quarter_str + '季度',
        }
        for field in field_list:
            model[field] = [0, '']

        for year_item in list(year_item_list):
            year_item_data = year_item['data']
            headers = year_item_data['headers']
            rows = year_item_data['rows']
            try:
                for row in rows:
                    if row[0] == target_row:
                        for field in field_list:
                            if field in headers:
                                index = headers.index(field)
                            else:
                                raise Exception('找不到对应字段')

                            if 'units' in year_item_data:
                                unit = year_item_data['units'][index]
                                if len(model[field][1]) == 0:
                                    model[field][1] = unit
                                elif model[field][1] != unit:
                                    raise Exception('单位不同步')

                            model[field][0] += int(row[index].replace(',', ''))
                        break
            except Exception as e:
                pass

        print(model)

    # print(result)


if __name__ == '__main__':
    # run() #  同步数据

    # do_statistics(start=2007, end=2018, target_row='全国合计', quarter_list=['1', '2', '3', '4'], field_list=['结婚登记', '离婚登记'])
    do_statistics(start=2019, end=2019, target_row='全国合计', quarter_list=['1', '2', '3', '4'],
                  field_list=['镇', '养老机构'])
