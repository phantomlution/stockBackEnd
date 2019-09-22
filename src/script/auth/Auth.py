'''
    获取第三方token
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Auth:
    pass

    # 获取 雪球网 token
    @staticmethod
    def get_snow_ball_auth():
        cookies = {}
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(chrome_options=options)
        driver.get('https://xueqiu.com/S/SZ000007')
        local_cookies = driver.get_cookies()
        cookie_fields_set = set([
            'xq_a_token',
            'xq_a_token.sig',
            'xq_r_token',
            'xq_r_token.sig'
        ])
        for cookie in local_cookies:
            cookie_name = cookie['name']
            cookie_value = cookie['value']
            if cookie_name in cookie_fields_set:
                cookies[cookie_name] = cookie_value
        driver.quit()
        return cookies

