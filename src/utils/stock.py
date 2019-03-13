#coding=utf-8
import requests
from bs4 import BeautifulSoup
import re

def loadHtml():
  response = requests.get('http://quote.eastmoney.com/stocklist.html')
  response.encoding = 'gb2312'
  return response.text

def getStockListHtml():
  raw_html = loadHtml()
  html = BeautifulSoup(raw_html, 'html.parser')
  stock_list = html.select('#quotesearch ul')
  return stock_list[0].select('li a')

def getStockList():
  stock_list_html = getStockListHtml()
  list = []
  for stock_item in stock_list_html:
    stock_text = stock_item.get_text()
    value = re.sub('\)', '', stock_text).split('(')
    list.append((value[0], value[1]))
  return list
