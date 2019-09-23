'''
    爬取金投网内的银行列表
'''

import requests
from bs4 import BeautifulSoup

# 提取银行列表
class BankList:

    def get_html(self):
        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
        }

        url = 'https://bank.cngold.org/lccp/daquan.html'
        response = requests.get(url, headers=headers)
        return response.text

    def get_bank_list(self):
        raw_html = self.get_html()

        html = BeautifulSoup(raw_html, 'html.parser')
        href_list = html.select('.list_yhwd a')

        bank_list = []
        for href in href_list:
            bank_list.append({
                "id": href['href'].split('_')[-1].split('.')[0],
                "name": href.text
            })

        return bank_list

class FinancialProductJob:
    pass
