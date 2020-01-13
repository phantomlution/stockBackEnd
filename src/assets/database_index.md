# 数据库的索引

db.getCollection('base').createIndex({"symbol": -1 })
db.getCollection('history').createIndex({"symbol": -1 })
db.getCollection('surge_for_short').createIndex({"code": -1,"date":-1})