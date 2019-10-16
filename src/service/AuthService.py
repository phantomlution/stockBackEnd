'''
    获取第三方token
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


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
