from src.service.StockService import StockService

client = StockService.getMongoInstance()

document = client.stock.surge_for_short

item_list = list(document.find({ "date": '2020-01-02'}))

short_list = []


for item in item_list:
    if item['result'] is not None:
        short_list.append(item)

print(len(short_list))
print(len(item_list))
