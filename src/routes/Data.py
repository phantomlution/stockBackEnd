'''
    数据相关内容
'''

from flask import Blueprint, request
from src.service.StockService import StockService
from src.service.DataService import DataService
from src.utils.decorator import flask_response
from src.script.extractor.centualBank import extractAllCentualBank
data_api = Blueprint('data_api', __name__, url_prefix='/data')

mongo = StockService.getMongoInstance()
sync_document = mongo.stock.sync
estate_document = mongo.stock.estate
huitong_document = mongo.stock.huitong


@data_api.route("/block/concept")
@flask_response
# 获取概念板块数据
def get_concept_block_data():
    return StockService.get_concept_block()


@data_api.route('/centralBank', methods=['GET'])
@flask_response
def get_central_bank_financial_info():
    return extractAllCentualBank()


@data_api.route('/shibor', methods=['GET'])
@flask_response
def get_financial_shibor():
    start = request.args.get('start')
    end = request.args.get('end')
    return DataService.get_shibor_data(start, end)


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
    return DataService.get_stat_info(code)


@data_api.route('/huitong/index')
@flask_response
def get_huitong_index_list():
    return list(huitong_document.find({}, { "_id": 0 }))