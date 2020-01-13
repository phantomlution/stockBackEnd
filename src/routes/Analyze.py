'''
    数据分析
'''

from flask import Blueprint, request
from src.service.AnalyzeService import AnalyzeService
from src.utils.decorator import flask_response
from src.service.FinancialService import get_history_fragment_trade_data, get_real_time_trade_data
analyze_api = Blueprint('analyze_api', __name__, url_prefix='/analyze')


# 获取历史分时成交数据
@analyze_api.route('/history/fragment/trade')
@flask_response
def get_history_fragment_trade():
    code = request.args.get('code')
    date = request.args.get('date')
    return get_history_fragment_trade_data(code, date)


# 获取实时数据
@analyze_api.route('/live/fragment/trade')
@flask_response
def get_live_fragment_trade():
    code = request.args.get('code')
    return get_real_time_trade_data(code)


@analyze_api.route('/restrict_sell', methods=['GET'])
@flask_response
def get_restrict_sell_date():
    return AnalyzeService.analyze_restrict_date()


# 判断是否存在拉高出货的点
@analyze_api.route('/surgeForShort/batch', methods=['PUT'])
@flask_response
def batch_get_surge_for_short():
    model = request.get_json()
    code = model.get('code')
    date_list = model['dateList']

    result = []
    for _date in date_list:
        result.append(AnalyzeService.get_surge_for_short(code, _date))
    return result


# 拉高出货点分析
@analyze_api.route('/surgeForShort', methods=['GET'])
@flask_response
def get_surge_for_short():
    code = request.args.get('code')
    _date = request.args.get('date')

    return AnalyzeService.get_surge_for_short(code, _date)


# 用于人工 确认/调整， 拉高出货点
@analyze_api.route('/surgeForShort', methods=['PUT'])
@flask_response
def update_surge_for_short():
    params = request.get_json()

    return AnalyzeService.update_surge_for_short(params)


# 全市场拉高出货分析
@analyze_api.route('/market/surge_for_short', methods=['POST'])
@flask_response
def get_market_surge_for_short():
    date_list = request.get_json()
    return AnalyzeService.get_market_surge_for_short(date_list)


# 临时分析数据
@analyze_api.route('/custom', methods=['GET'])
@flask_response
def get_temporary_analyze():
    # return AnalyzeService.get_stunt_point_list()
    return AnalyzeService.get_low_amount_restrict_sell()


@analyze_api.route('/concept/block/trend')
@flask_response
def get_concept_block_trend():
    return AnalyzeService.get_concept_block_ranking()


@analyze_api.route('/stock/list', methods=['POST'])
@flask_response
def insert_stock_list():
    stock_list = request.get_json()
    AnalyzeService.update_stock_list(stock_list)
