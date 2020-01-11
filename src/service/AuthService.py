'''
    获取第三方token
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from src.service.HtmlService import get_response
import re


class AuthService:

    # 获取 雪球网 token
    @staticmethod
    def get_snow_ball_auth():
        cookies = {}
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(chrome_options=options)
        driver.get('https://xueqiu.com/S/SZ000007')
        local_cookies = driver.get_cookies()
        driver
        for cookie in local_cookies:
            cookies[cookie['name']] = cookie['value']
        driver.quit()

        return cookies

    @staticmethod
    def get_cookie_str(url):
        options = Options()
        options.headless = True
        options.add_argument("–incognito")

        driver = webdriver.Chrome(chrome_options=options)
        driver.get(url)
        local_cookies = driver.get_cookies()

        cookie_str = ''
        for cookie in local_cookies:
            if len(cookie_str) > 0:
                cookie_str += '; '
            cookie_str += cookie['name']
            cookie_str += '='
            cookie_str += cookie['value']
        driver.quit()
        return cookie_str

    @staticmethod
    def get_east_money_token():
        url = 'http://data.eastmoney.com/js_001/hsgt/hsgt.js'

        raw_html = get_response(url)

        raw_html = str(raw_html)

        match_obj = re.search(r'&token=([a-zA-Z0-9]+)&', raw_html)

        if match_obj is None:
            raise Exception('EastMoney token 获取错误')

        return match_obj.groups()[0]
