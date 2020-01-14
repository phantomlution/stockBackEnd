# 数据库的索引

db.getCollection('base').createIndex({"symbol": -1, "type": 1 })
db.getCollection('history').createIndex({"symbol": -1 })
db.getCollection('surge_for_short').createIndex({"code": -1,"date":-1})
db.getCollection('notification').createIndex({"has_read": 1 })
db.getCollection('news').createIndex({"has_read": 1 })
db.getCollection('notice').createIndex({"stock_code": 1 })
db.getCollection('concept_block_ranking').createIndex({"date": -1 })