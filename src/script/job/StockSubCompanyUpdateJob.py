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
from src.service.AuthService import AuthService

client = StockService.getMongoInstance()
base_document = client.stock.base

search_base = 'http://www.qichacha.com'


class StockSubCompanyUpdateJob:

    def __init__(self):
        stock_list = DataProvider().get_stock_list()
        self.cookie = None
        self.job = Job(name='关联子公司数据同步')
        self.request_interval = 2
        for stock in stock_list:
            self.job.add(stock)

    def get_interval(self):
        return random.random() * self.request_interval

    def get_search_list_html(self, company_name):
        time.sleep(self.get_interval())
        url = search_base + '/search'
        params = {
            "key": company_name
        }

        headers = {
            'cookie': self.cookie,
            "Host": "www.qichacha.com",
            "Referer": "http://www.qichacha.com/"
        }

        response = get_response(url, headers=headers, params=params)

        return response

    def get_company_url(self, company_name, code):
        raw_html = self.get_search_list_html(company_name)
        html = BeautifulSoup(raw_html, 'html.parser')
        result_list = html.select('#search-result tr')
        if len(result_list) == 0:
            print('{},{}'.format(company_name, code))
            raise Exception('未找到结果')

        first_item = result_list[0]

        tag = first_item.select_one('.search-tags').text
        stock_tag = code[2:] + '.' + code[:2]
        if stock_tag not in tag:
            print(tag)
            raise Exception('公司不匹配')

        href_item = first_item.select_one('a')
        href = href_item['href']

        company_url = search_base + href

        return company_url

    def get_company_detail(self, company_url):
        time.sleep(self.get_interval())
        headers = {
            "cookie": self.cookie,
            "Host": "www.qichacha.com"
        }
        raw_html = get_response(company_url, headers=headers)
        html = BeautifulSoup(raw_html, 'html.parser')
        company_table = html.select_one('#cgkgList table')
        if company_table is None:
            print(company_table)
            raise Exception('找不到对应信息')
        table_result = extract_table(company_table)

        header = table_result[0]
        body = table_result[1:]

        if header[1] != '企业名称' or header[2] != '参股关系' or header[3] != '参股比例' or header[-1] != '主营业务':
            print(header)
            raise Exception('列信息错位')

        result = []
        for sub_company in body:
            result.append({
                "name": str.strip(sub_company[1]),
                "relation": str.strip(sub_company[2]),
                "stock_share": str.strip(sub_company[3]),
                "main_business": str.strip(sub_company[-1])
            })

        return result

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def start(self):
        count = -1
        for task in self.job.task_list:
            task_id = task['id']
            stock = task['raw']
            code = stock['code']
            stock_base = base_document.find_one({ "symbol": code })
            if 'sub_company_list' not in stock_base:
                count += 1
                # if count % 10 == 0:
                #     self.cookie = AuthService.get_cookie_str(search_base)

                company_name = stock_base['company']['org_name_cn']
                company_url = self.get_company_url(company_name, code)
                sub_company_list = self.get_company_detail(company_url)

                base_document.update({'symbol': code}, {'$set': {'qichacha_url': company_url}}, True)
                base_document.update({'symbol': code}, { '$set': {'sub_company_list': sub_company_list }}, True)

            self.job.success(task_id)
