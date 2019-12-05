'''
    数据分析
'''

from flask import Blueprint, request
from src.service.AnalyzeService import AnalyzeService
from src.utils.decorator import flask_response
from src.service.FinancialService import get_history_fragment_trade_data
analyze_api = Blueprint('analyze_api', __name__, url_prefix='/analyze')


# 获取历史分时成交数据
@analyze_api.route('/history/fragment/trade')
@flask_response
def get_history_fragment_trade():
    code = request.args.get('code')
    date = request.args.get('date')
    return get_history_fragment_trade_data(code, date)


@analyze_api.route('/restrict_sell', methods=['GET'])
@flask_response
def get_restrict_sell_date():
    return AnalyzeService.analyze_restrict_date()