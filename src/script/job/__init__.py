from src.service.StockService import StockService
client = StockService.getMongoInstance()
bond_document = client.stock.bond

_set = set()

for item in bond_document.find({}):
    if item['data'] is not None:
        _set.add(item['data']['pay_interest_duration'])

print(_set)