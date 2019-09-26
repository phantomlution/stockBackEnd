import requests
from bs4 import BeautifulSoup
from urllib import parse


url = 'https://www.fmprc.gov.cn/web/fyrbt_673021/dhdw_673027/'

response = requests.get(url).content.decode()
html = BeautifulSoup(response, 'html.parser')

src_element_list = html.find_all(src=True)
for src_element in src_element_list:
    src_element['src'] = parse.urljoin(url, src_element['src'])
    print(src_element)

href_element_list = html.find_all(href=True)
for href_element in href_element_list:
    src_element['href'] = parse.urljoin(url, src_element['href'])
