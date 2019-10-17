'''
    关联上市公司的子公司
    数据源：企查查
'''
from src.service.HtmlService import get_response, extract_table
from bs4 import BeautifulSoup
from src.assets.DataProvider import DataProvider
from src.script.job.Job import Job
from src.service.StockService import StockService
import time
import random

client = StockService.getMongoInstance()
base_document = client.stock.base

search_base = 'https://www.qichacha.com'


class StockSubCompanyUpdateJob:

    def __init__(self):
        stock_list = DataProvider().get_stock_list()
        self.cookie = None
        self.job = Job(name='关联子公司数据同步')
        self.request_interval = 2
        for stock in stock_list:
            self.job.add(stock)

    def get_interval(self):
        return 3 + random.random() * self.request_interval

    def get_search_list_html(self, company_name):
        time.sleep(self.get_interval())
        url = search_base + '/search'
        params = {
            "key": company_name
        }

        headers = {
            'Cookie': self.cookie,
            "Host": "www.qichacha.com",
            "Referer": "https://www.qichacha.com/"
        }

        response = get_response(url, headers=headers, params=params)

        return response

    def get_stock_tag(self, code):
        return code[2:] + '.' + code[:2]

    def get_company_detail(self, company_url, code):
        headers = {
            "cookie": self.cookie,
            "Host": "www.qichacha.com"
        }
        time.sleep(self.get_interval())
        raw_html = get_response(company_url, headers=headers)
        html = BeautifulSoup(raw_html, 'html.parser')

        company_header = html.select_one('#company-top .content .row.tags').text
        stock_tag = self.get_stock_tag(code)

        if stock_tag not in company_header:
            raise Exception('数据不匹配')

        company_table = html.select_one('#cgkgList table')
        stock_holder_table = html.select_one('#gdList table')

        sub_company_list = []
        if company_table is not None:
            table_result = extract_table(company_table)

            header = table_result[0]

            if header[1] != '企业名称' or header[2] != '参股关系' or header[3] != '参股比例' or header[-1] != '主营业务':
                print(header)
                raise Exception('子公司，列信息错位')

            company_table_row_list = company_table.select('tr')
            for row_index, row in enumerate(company_table_row_list):
                if row_index == 0:
                    continue

                model = {
                    "company_name": '',
                    "company_href": '',
                    'relation': '',
                    'stock_share': '',
                    'main_business': ''
                }

                for column_index, column in enumerate(row.select('td')):
                    if column_index == 1:
                        company_detail_html = column.select_one('.whead-text')
                        company_href = company_detail_html.select_one('a')
                        if company_href is not None:
                            model['company_name'] = str.strip(company_href.text)
                            model["company_href"] = company_href['href']
                        else:
                            model["company_name"] = str.strip(company_detail_html.text)
                    elif column_index == 2:
                        model["relation"] = str.strip(column.text.split('%')[0])
                    elif column_index == 3:
                        model['stock_share'] = str.strip(column.text)
                    elif column_index == len(header) - 1:
                        model['main_business'] = str.strip(column.text)

                sub_company_list.append(model)

        stock_holder_list = []
        if stock_holder_table is not None:
            stock_holder_table_row_list = stock_holder_table.select('tr')
            stock_holder_table_result = extract_table(stock_holder_table)
            stock_holder_table_header = stock_holder_table_result[0]
            if stock_holder_table_header[1] != '股东名称' or stock_holder_table_header[4] != '持股比例':
                print(stock_holder_table_header)
                raise Exception('股东信息，列信息错位')
            for row_index, row in enumerate(stock_holder_table_row_list):
                if row_index == 0:
                    continue

                model = {
                    "company_name": '',
                    "company_href": '',
                    'stock_percent': ''
                }

                for column_index, column in enumerate(row.select('td')):
                    if column_index == 1:
                        company_detail_html = column.select_one('.whead-text')
                        company_href = company_detail_html.select_one('a')
                        if company_href is not None:
                            model['company_name'] = str.strip(company_href.text)
                            model["company_href"] = company_href['href']
                        else:
                            model["company_name"] = str.strip(company_detail_html.text)
                    elif column_index == 4:
                        model["stock_percent"] = str.strip(column.text.split('%')[0])

                stock_holder_list.append(model)

        return {
            "sub_company_list": sub_company_list,
            "stock_holder_list": stock_holder_list
        }

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        for task in self.job.task_list:
            task_id = task['id']
            stock = task['raw']
            code = stock['code']
            stock_base = base_document.find_one({ "symbol": code })
            if 'stock_holder_list' not in stock_base:
                if 'qichacha_url' not in stock_base or stock_base['qichacha_url'] is None:
                    raise Exception('请先同步企查查url: [qichachaUrl.py]')

                company_url = stock_base['qichacha_url']
                print('current code: {}, url: {}'.format(stock_base['symbol'], company_url))
                company_detail = self.get_company_detail(company_url, code)

                sub_company_list = company_detail['sub_company_list']
                stock_holder_list = company_detail['stock_holder_list']

                base_document.update({'symbol': code}, {'$set': {'qichacha_url': company_url}}, True)
                base_document.update({'symbol': code}, {'$set': {'sub_company_list': sub_company_list}}, True)
                base_document.update({"symbol": code}, {'$set': {'stock_holder_list': stock_holder_list}}, True)
            self.job.success(task_id)


if __name__ == '__main__':
    StockSubCompanyUpdateJob().run()