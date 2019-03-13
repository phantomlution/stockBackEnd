from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
database = client.stock
historyDocument = database.history

blackList = []

for item in historyDocument.find():
    if item['count'] == 420:
        data = item['data']
        for dataItem in list(data):
            if abs(dataItem['percent']) > 15:
                blackList.append(item['code'])
                break


print(blackList)