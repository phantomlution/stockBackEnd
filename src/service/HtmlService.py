'''
    的html
'''
import requests
from bs4 import BeautifulSoup
from urllib import parse
import json
import re
from src.utils.extractor import Extractor


def extract_jsonp(response, jsonp):
    content = str(response)[len(jsonp) + 1:-1]
    return json.loads(content)


def get_response(url, headers=None, params=None, encoding='utf-8'):
    request_headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
    }
    if headers is not None:
        for header in headers:
            request_headers[header] = headers[header]

    response = requests.get(url, headers=request_headers, params=params)

    content_type = response.headers['content-type'].split(';')
    for content_type in content_type:
        content_type_str = str.strip(content_type).lower()
        if 'charset' in content_type_str:
            encoding = content_type_str.split('=')[-1]
            break
    if len(encoding) > 0:
        return response.content.decode(encoding)
    else:
        return response.content.decode()


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


# 抓取html中的变量
def get_html_variable(raw_html, name):
    pattern = re.compile('[(var)(let)(const)]\s*' + name + '\s*=\s*(.*?);')
    find_result = pattern.findall(raw_html)

    if len(find_result) == 1:
        return json.loads(find_result[0])
    else:
        return None


# 提取表格数据
def extract_table(content_doc):
    extractor = Extractor(content_doc)
    extractor.parse()
    return_list = extractor.return_list()

    return return_list