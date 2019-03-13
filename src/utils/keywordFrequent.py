#coding=utf-8
import requests
import json
import time

# cookie过期的话需要重新设置

headers = {
  "referer": "http://index.baidu.com/v2/main/index.html",
  "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
  "cookie": "BIDUPSID=04795685BE7F5D48E53B41B59E672AE2; PSTM=1538097567; BAIDUID=F4256DB980E8615E3BD873D1A9998558:FG=1; bdshare_firstime=1548745571293; MCITY=-179%3A; pgv_pvi=3826569216; Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc=1548745569,1549850398; BDRCVFR[feWj1Vr5u3D]=I67x6TjHwwYf0; delPer=0; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; BCLID=11284972334863274576; BDSFRCVID=ui4OJeCwMCHW4io9DQQT2ha2XDq8vlRTH6aoycuEWddl0-3S9WqZEG0PJM8g0Ku-Fu6TogKKKgOTHICF_2uxOjjg8UtVJeC6EG0P3J; H_BDCLCKID_SF=tR4JVIKMJKt3fP36qRbshn-_KMuX5-RLf5T0_p7F5lOb8qOS3TOEhTFv0JQnJtvKtHbRQCnKaUoxOKQphnrj5fLibMOQJIueLb5UQxcN3KJmOlC9bT3v5Duz5Hjn2-biW23M2MbdWlOP_IoG2Mn8M4bb3qOpBtQmJeTxoUtbWDcjqR8ZDjt2ejQP; PSINO=7; H_PS_PSSID=26525_1423_21093_28328; CHKFORREG=397cebd7a288e2906c5a4e06095a6961; bdindexid=1a23ks61kq6fth9f916358pbj0; BDUSS=2xMWDJtVTIzbDlWMFlZd3hVanBLUGZ2Q3dFc3NkdHNscUFWNlozZEpLZVl5b2hjQVFBQUFBJCQAAAAAAAAAAAEAAACErJmrZmFmc2Rmc2RmamxqawAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJg9YVyYPWFcQ; Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc=1549876667"
}

def fancyPrint(parsed):
  print(json.dumps(parsed, indent=4, sort_keys=True))

def loadData(keyword, days):
  payload = {
    "word": keyword,
    "area": "0",
    "days": days
  }
  url = 'http://index.baidu.com/api/SearchApi/index'
  r = requests.get(url, headers=headers, params=payload)
  allDataJson = json.loads(r.content)['data']
  allData = allDataJson['userIndexes'][0]['all']
  rawData = allData['data']

  return {
    "id": allDataJson['uniqid'],
    "data": rawData
  }

def loadDecodeKey(uniqueId):
  payload = {
    "uniqid": uniqueId
  }
  url = 'http://index.baidu.com/Interface/ptbk'
  r = requests.get(url, headers=headers, params=payload)
  response = json.loads(r.content)['data']
  return response

def decrypt(t, e):
  n = list(t)
  i = list(e)
  r = {}
  a = []

  for o in range(len(n) // 2):
    r[n[o]] = n[len(n) // 2 + o]

  for s in range(len(e)):
    a.append(str(r[i[s]]))
  return ''.join(a)

def search(word, days):
  rawData = loadData(word, days)
  decodeKey = loadDecodeKey(rawData["id"])
  result = decrypt(decodeKey, rawData['data'])
  finalResult = result.split(',')
  return finalResult
