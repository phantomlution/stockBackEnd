'''
    数据相关内容
'''

from flask import Blueprint, request
from src.service.StockService import StockService
from src.service.DataService import DataService
from src.service.DataWorker import DataWorker
from src.utils.decorator import flask_response
from src.service.FxWorker import FxWorker
data_api = Blueprint('data_api', __name__, url_prefix='/data')

mongo = StockService.getMongoInstance()
sync_document = mongo.stock.sync
estate_document = mongo.stock.estate
huitong_document = mongo.stock.huitong
concept_block_ranking_document = mongo.stock.concept_block_ranking


@data_api.route("/block/concept")
@flask_response
# 获取概念板块数据
def get_concept_block_data():
    return StockService.get_concept_block()


@data_api.route('/shibor', methods=['GET'])
@flask_response
def get_financial_shibor():
    start = request.args.get('start')
    end = request.args.get('end')
    return DataWorker.get_shibor_data(start, end)


@data_api.route('/estate/date/list', methods=['GET'])
@flask_response
def get_estate_date_list():
    result = []
    date_list = sync_document.find({"key": { "$regex": "^estate"}, "done": True })
    for date in date_list:
        result.append( date['key'].split('_')[1])

    return result


@data_api.route('/estate', methods=['GET'])
@flask_response
def get_estate_data():
    date = request.args.get('date')

    return list(estate_document.find({ "date": date }, { "_id": 0 }))


@data_api.route('/stat/country', methods=['GET'])
@flask_response
def get_country_stat():
    code = request.args.get('code')
    return DataWorker.get_stat_info(code)


@data_api.route('/huitong/index')
@flask_response
def get_huitong_index_list():
    return list(huitong_document.find({}, { "_id": 0 }))


# 获取财经事件
@data_api.route('/calendar')
@flask_response
def get_calendar():
    _date = request.args.get('date')
    return DataWorker.get_financial_event_calendar(_date)


# 获取最近的市场交易日列表，目前按照history表中上证指数的数据点个数
@data_api.route('/recent/market/open')
@flask_response
def get_recent_open_date_list():
    return DataWorker.get_recent_open_date_list()


@data_api.route('/search/option')
@flask_response
def get_search_option_list():
    return DataService.get_search_option_list()


@data_api.route('/sync/fragment/deal')
@flask_response
def get_sync_item_fragment_deal():
    secid = request.args.get('secid')
    _date = request.args.get('date')

    return DataWorker.get_sync_fragment_deal(secid, _date)


# 获取央行会议信息
@data_api.route('/fx/centralBank/schedule', methods=['GET'])
@flask_response
def get_central_bank_financial_info():
    return FxWorker.get_central_bank_schedule_list()


@data_api.route('/concept/ranking', methods=['PUT'])
@flask_response
def get_concept_block_ranking():
    params = request.get_json()
    date_list = params['dateList']
    return DataService.get_concept_block_ranking(date_list)


@data_api.route('/base', methods=['GET'])
@flask_response
def get_base():
    code = request.args.get('code')
    return DataService.get_base(code)


# 获取k线
@data_api.route('/kline', methods=['GET'])
@flask_response
def get_kline():
    code = request.args.get('code')
    return DataService.get_kline(code)


# 获取商品报价（主要用于显示初始化，读取历史价位）
@data_api.route('/quote')
@flask_response
def get_fx_quote():
    code = request.args.get('code')
    return DataService.get_quote(code)


