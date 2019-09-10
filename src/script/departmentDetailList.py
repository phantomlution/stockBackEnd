# 获取所有房源的详细信息

from src.utils.sessions import FuturesSession
from bs4 import BeautifulSoup
import json
import re

session = FuturesSession(max_workers=50)

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Referer": "http://zl.hzfc.gov.cn/webrent/projectlist.htm",
    "Cookie": "ROUTEID=.lb1; Hm_lvt_d9cfe436a15e8d2b9772889f9934ca4c=1562459540; JSESSIONID=50B331462B0A499DF4A3CA315B3D2BB7.lb1; Hm_lpvt_d9cfe436a15e8d2b9772889f9934ca4c=1562459646"
}

departmentDetailList = []

def getTableText(raw):
    return raw.text.split(' ')[0].split('：')[1]

def loadDepartmentDetail(item):
    url = "http://zl.hzfc.gov.cn" + item
    r = session.get(url, headers=headers)
    html = r.result().content.decode()
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.findAll('li', class_='bigT')[0].font.text
    tableItemList = soup.findAll('td')
    address = getTableText(tableItemList[0])
    roomCount = getTableText(tableItemList[3])
    rent = getTableText(tableItemList[4])
    regexResult = re.search(r'QueryPRJ.*', html)
    positionInfo = regexResult.group().split('\',\'')
    model = {
        "url": url,
        "id": item,
        "title": title,
        "roomCount": roomCount,
        "address": address,
        "rent": rent,
        "longitude": positionInfo[1],
        'latitude': positionInfo[2]
    }
    departmentDetailList.append(model)

def loadAllData():
    with open('./departmentList.json', 'r') as file:
        itemList = json.load(file)
    for item in itemList:
        loadDepartmentDetail(item)
