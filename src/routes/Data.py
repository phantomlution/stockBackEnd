'''
    数据相关内容
'''

from flask import Blueprint
from src.service.StockService import StockService
from src.utils.decorator import flask_response
data_api = Blueprint('data_api', __name__, url_prefix='/data')


@data_api.route("/block/concept")
@flask_response
# 获取概念板块数据
def get_concept_block_data():
    return StockService.get_concept_block()