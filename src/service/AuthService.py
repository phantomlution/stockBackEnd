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
            cookies[cookie.name] = cookie['value']
        driver.quit()
        print(cookies)
        return cookies

    @staticmethod
    def get_cookie_str(url):
        cookies = {}
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(chrome_options=options)
        driver.get(url)
        local_cookies = driver.get_cookies()

        cookie_str = ''
        for cookie in local_cookies:
            if len(cookie_str) > 0:
                cookie_str += '; '
            cookie_str += cookie['name']
            cookie_str += '='
            if cookie['name'] == 'acw_tc':
                cookie_str += 'df6ff44315711486182285510e01be2a795068cc8c58a8e85d7dcd27ce'
            else:
                cookie_str += cookie['value']
        driver.quit()
        return cookie_str
