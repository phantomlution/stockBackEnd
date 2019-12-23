'''
    股票相关内容
'''
from flask import Blueprint, request
from src.service.StockService import StockService
from src.assets.DataProvider import DataProvider
from src.utils.decorator import flask_response
stock_api = Blueprint('stock_api', __name__, url_prefix='/stock')

mongo = StockService.getMongoInstance()
hot_money_document = mongo.stock.hotMoney
theme_document = mongo.stock.theme
theme_market_document = mongo.stock.theme_market
history_document = mongo.stock.history


@stock_api.route('/detail', methods=['GET'])
@flask_response
def detail():
    code = request.args.get('code')
    return {
        "base": StockService.get_stock_base(code),
        "data": StockService.get_history_data(code)
    }


@stock_api.route('/base', methods=['GET'])
@flask_response
def get_stock_base():
    code = request.args.get('code')
    return StockService.get_stock_base(code)


@stock_api.route('/trade/data')
@flask_response
# 获取指定交易日的交易数据
def get_trade_data():
    date = request.args.get('date')
    code = request.args.get('code')

    return StockService.get_trade_data(code, date)


@stock_api.route('/list')
@flask_response
def get_stock_list():
    return DataProvider().get_stock_list()


@stock_api.route('/capital/hotMoney')
@flask_response
def get_hot_money():
    date = request.args.get('date')
    is_live = request.args.get('live')

    if str.lower(is_live) == 'true':
        result = StockService.get_hot_money_data()
    else:
        result = hot_money_document.find_one({ "date": date }, { "_id": 0 })

    return result


@stock_api.route('/notice')
@flask_response
def get_notice():
    code = request.args.get('code')
    return StockService.load_stock_notice(code)


@stock_api.route('/theme', methods=['GET'])
@flask_response
def get_stock_theme_list():
    result = theme_document.find({}, { "_id": 0 })
    return list(result)


@stock_api.route('/theme/market', methods=['GET'])
@flask_response
def get_stock_theme_market():
    theme_market_list = theme_market_document.find({}, { "_id": 0 })
    return list(theme_market_list)


# 查询某一个十大股东，目前能查到的所有持股信息
@stock_api.route('/share/all', methods=['GET'])
@flask_response
def get_all_company_stock_share():
    url = request.args.get('url')
    return StockService.get_all_stock_share_company(url)


@stock_api.route('/detail/pledge')
@flask_response
def get_stock_pledge():
    code = request.args.get('code')
    return StockService.get_pledge_rate(code)


@stock_api.route('/detail/biding')
@flask_response
def get_stock_biding():
    code = request.args.get('code')
    return StockService.get_stock_biding(code)
