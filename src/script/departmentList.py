# 获取所有房源列表

from src.utils.sessions import FuturesSession
from bs4 import BeautifulSoup

session = FuturesSession(max_workers=50)

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Referer": "http://zl.hzfc.gov.cn/webrent/projectlist.htm",
    "Cookie": "ROUTEID=.lb1; Hm_lvt_d9cfe436a15e8d2b9772889f9934ca4c=1562459540; JSESSIONID=50B331462B0A499DF4A3CA315B3D2BB7.lb1; Hm_lpvt_d9cfe436a15e8d2b9772889f9934ca4c=1562459646"
}

url = 'http://zl.hzfc.gov.cn/webrent/projectlist.htm'

targetUrlList = []

# 获取id列表
def collectTargetId(html):
    soup = BeautifulSoup(html, 'html.parser')
    divList = soup.findAll('div', class_="xiaoquShow")
    for div in divList:
        for children in div.children:
            if len(children) > 1:
                try:
                    href = children['href']
                    targetUrlList.append(href)
                except:
                    pass

# 获取所有的数据
def loadAllData():
    pageCount = 37
    for pageIndex in range(pageCount - 1):
        formData = {
            "page": pageIndex + 1
        }
        r = session.post(url, formData, headers=headers)
        result = r.result().content.decode()
        collectTargetId(result)

loadAllData()

# 打印所有房源
print(targetUrlList)