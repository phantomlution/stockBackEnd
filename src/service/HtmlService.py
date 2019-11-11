'''
    的html
'''
import requests
from bs4 import BeautifulSoup
from urllib import parse
import json
import re
from src.utils.extractor import Extractor
from requests.adapters import HTTPAdapter


def extract_jsonp(response, jsonp):
    content = str(response)[len(jsonp) + 1:str.rindex(response, ')')]
    return json.loads(content)


session = requests.Session()
session.mount('http://', HTTPAdapter(max_retries=3))
session.mount('https://', HTTPAdapter(max_retries=3))


def get_response(url, headers=None, params=None, encoding=None, use_proxy=False):
    if use_proxy:
        proxy = {
            "http": "socks5://127.0.0.1:1086",
            "https": 'socks5://127.0.0.1:1086'
        }
    else:
        proxy = None
    request_headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
    }
    if headers is not None:
        for header in headers:
            request_headers[header] = headers[header]

    response = session.get(url, headers=request_headers, params=params, proxies=proxy, timeout=5)

    result = {
        "response": ''
    }
    if encoding is not None:
        result['response'] = response.content.decode(encoding)
    else:
        if 'content-type' in response.headers:
            content_type = response.headers['content-type'].split(';')
            for content_type in content_type:
                content_type_str = str.strip(content_type).lower()
                if 'charset' in content_type_str:
                    encoding = content_type_str.split('=')[-1]
                    break
        if encoding is not None and len(encoding) > 0:
            result['response'] = response.content.decode(encoding)
        else:
            result['response'] = response.content.decode('utf-8')

    response.close()
    return result['response']


# 爬取页面后，将页面中相对路径全部转换成为绝对路径
def get_parsed_href_html(url, response):
    html = BeautifulSoup(response, 'html.parser')

    # 转换相对路径为绝对路径
    src_element_list = html.find_all(src=True)
    for src_element in src_element_list:
        src_element['src'] = get_absolute_url_path(url, src_element['src'])

    href_element_list = html.find_all(href=True)
    for href_element in href_element_list:
        href_element['href'] = get_absolute_url_path(url, href_element['href'])

    return str(html)


# 抓取html中的变量
def get_html_variable(raw_html, name, variable_define=True):
    # variable_define 判断是否需要变量定义
    prefix_str = '[^/]+'
    define_str = '[(var)(let)(const)]'
    search_pattern = '\s*' + name + '\s*=\s*(.*?);'
    if variable_define:
        pattern = re.compile(prefix_str + define_str + search_pattern)
    else:
        pattern = re.compile(prefix_str + search_pattern)
    find_result = pattern.findall(raw_html)

    if len(find_result) == 1:
        return json.loads(find_result[0])
    else:
        return None


def get_absolute_url_path(target, relative_url):
    return parse.urljoin(target, relative_url)


# 提取表格数据
def extract_table(content_doc):
    extractor = Extractor(content_doc)
    extractor.parse()
    return_list = extractor.return_list()

    return return_list

