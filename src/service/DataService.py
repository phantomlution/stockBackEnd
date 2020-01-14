'''
    用于路由层提取数据
'''

from src.service.DatabaseService import DatabaseService
from src.service.FxWorker import FxWorker
from src.service.EastMoneyWorker import EastMoneyWorker
from src.service.HtmlService import get_response
from bs4 import BeautifulSoup


class DataService:

    @staticmethod
    def get_quote(code):
        return FxWorker.get_quote(code)

    @staticmethod
    def get_kline(code):
        base = DatabaseService.get_base(code)
        source = base['source']
        if source == 'fx':
            return FxWorker.get_kline(code)
        else:
            result = DatabaseService.get_history_data(code)
            if result is None or len(result) == 0:
                if 'secid' in base:
                    return EastMoneyWorker.get_kline(base['secid'])
            return result

    @staticmethod
    def get_base(code):
        return DatabaseService.get_base(code)

    # 获取搜索项
    @staticmethod
    def get_search_option_list():
        result_model = {}
        item_list = DatabaseService.get_base_item_list()

        def get_type_label(val):
            if val == 'index':
                return '指数'
            elif val == 'concept':
                return '板块'
            elif val == 'capital':
                return '资金'
            elif val == 'coin':
                return '虚拟货币'
            elif val == 'exchange':
                return '外汇'
            else:
                return '股票'

        for item in item_list:
            _type = item['type']
            if _type not in result_model:
                result_model[_type] = {
                    "label": get_type_label(_type),
                    "value": _type,
                    "children": []
                }
            label = item['name']
            value = item['symbol']
            if _type == 'stock':
                label = label + '(' + value + ')'
            result_model[_type]['children'].append({
                "label": label,
                "value": value
            })

        result = []
        for key in result_model:
            result.append(result_model[key])

        return result

    @staticmethod
    def get_concept_block_ranking(date_list):
        return DatabaseService.get_concept_block_ranking(date_list)


if __name__ == '__main__':
    print('')
