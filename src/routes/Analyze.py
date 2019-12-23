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