'''
    股票池
'''
from flask import Blueprint, request
from src.service.StockService import StockService
from src.utils.decorator import flask_response
stock_pool_api = Blueprint('stock_pool_api', __name__, url_prefix='/stock/pool')


@stock_pool_api.route('', methods=['GET'])
@flask_response
def get_stock_pool():
    return StockService.get_stock_pool()


@stock_pool_api.route('', methods=['POST'])
@flask_response
def add_to_stock_pool():
    item = request.get_json()
    StockService.add_stock_pool(item)
    return {}


@stock_pool_api.route('', methods=['DELETE'])
@flask_response
def remove_from_stock_pool():
    code = request.args.get('code')
    return StockService.remove_stock_pool(code)


@stock_pool_api.route('/item', methods=['GET'])
@flask_response
def get_stock_pool_item():
    code = request.args.get('code')
    return StockService.get_stock_pool_item(code)


# 获取预披露的公告信息
@stock_pool_api.route('/prerelease/calendar', methods=['GET'])
@flask_response
def get_stock_pool_pre_release_calendar():
    stock_list = StockService.get_stock_pool()
    result = []
    for stock in stock_list:
        result.append({
            "code": stock['code'],
            "name": stock['name'],
            "list": StockService.load_pre_release_notice(stock['code'])
        })

    return result


