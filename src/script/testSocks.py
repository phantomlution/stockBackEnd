#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import requests

# config-start
testUrl = "https://www.google.com"
timeout = 5 # 设置超时
threadNumber = 50 # 设置线程数
proxiesFileName = "proxies.txt"
successFileName = "success.txt"
# config-end

def testOnline(ip,port,protocol):
    '''
    测试HTTP代理是否可用
        利用IP138的接口 , 在响应的页面中寻找本机IP , 如果找到 , 则说明代理可以成功连接
    '''
    global successFileName
    global testUrl
    global timeout

    if protocol == "HTTPS":
        proxies = {"http":"http://"+ip+":"+port,"https":"http://"+ip+":"+port               }
    elif protocol == "SOCKS5":
        proxies = {"http":"socks5://"+ip+":"+port,"https":"socks5://"+ip+":"+port}
    else: # 不指定协议时使用HTTP协议
        proxies = {"http":"http://"+ip+":"+port,"https":"http://"+ip+":"+port}

    try:
        content=requests.get(testUrl,proxies=proxies,timeout=timeout).text.encode('UTF-8')
        print('Gotcha...Proxy Success')
    except Exception as e:
        # print e
        print("NetWork Error...")

class myThread (threading.Thread):
    def __init__(self, ip, port, protocol):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.protocol = protocol
    def run(self):
        testOnline(self.ip,self.port,self.protocol)

proxies=open(proxiesFileName,"r")

threads = [] # 线程池

for proxy in proxies:
    line = proxy[0:-1]
    ip = line.split(":")[0] # 获取IP
    port = line.split(":")[1].split("@")[0] # 获取端口
    # protocol = line.split(":")[1].split("@")[1].split("#")[0]
    protocol = 'SOCKS5'
    threads.append(myThread(ip,port,protocol))

for t in threads:
    t.start()
    while True:
        if(len(threading.enumerate())<threadNumber):
            break