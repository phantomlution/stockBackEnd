'''
    的html
'''
import requests
from bs4 import BeautifulSoup
from urllib import parse
import json


def extract_jsonp(response, jsonp):
    content = str(response)[len(jsonp) + 1:-1]
    return json.loads(content)

def get_response(url, headers=None, params=None):
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
    }
    if headers is not None:
        for header in headers:
            default_headers[header] = headers[header]

    return requests.get(url, headers=headers, params=params).content.decode()

# 爬取页面后，将页面中相对路径全部转换成为绝对路径
def get_parsed_href_html(url):
    response = get_response(url)
    html = BeautifulSoup(response, 'html.parser')

    # 转换相对路径为绝对路径
    src_element_list = html.find_all(src=True)
    for src_element in src_element_list:
        src_element['src'] = parse.urljoin(url, src_element['src'])

    href_element_list = html.find_all(href=True)
    for href_element in href_element_list:
        href_element['href'] = parse.urljoin(url, href_element['href'])

    return str(html)