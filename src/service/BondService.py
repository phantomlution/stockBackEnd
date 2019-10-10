from src.service.StockService import StockService
client = StockService.getMongoInstance()
bond_document = client.stock.bond
base_document = client.stock.base


class BondService:

    @staticmethod
    def get_stock_bond_list():
        company_name_arr = []
        name_map = {}
        for item in base_document.find({}, { "company.org_name_cn": 1, "symbol": 1, "_id": 0}):
            stock_company_name = item['company']['org_name_cn']
            if stock_company_name is not None and len(stock_company_name) > 0:
                stock_symbol = item['symbol']
                name_map[stock_company_name] = {
                    "symbol": stock_symbol,
                    "bondList": []
                }
                company_name_arr.append(stock_company_name)

        bond_count = 0
        for item in bond_document.find({ "data.publish_company": { "$in": company_name_arr }, "bond_type_name": { "$not": { "$eq": '同业存单' } } }, { "_id": 0 }):
            bond_company_name = item['data']['publish_company']
            name_map[bond_company_name]['bondList'].append(item)
            bond_count += 1

        result = []
        for key in name_map:
            if len(name_map[key]['bondList']) > 0:
                result.append({
                    "company": key,
                    "symbol": name_map[key]['symbol'],
                    "bondList": name_map[key]['bondList']
                })

        return result
