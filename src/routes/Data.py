from flask import Blueprint
from src.service.StockService import StockService
from src.utils.HttpUtils import success, fail
data_api = Blueprint('data_api', __name__, url_prefix='/data')


@data_api.route("/block/concept")
# 获取概念板块数据
def get_concept_block_data():
    return success(StockService.get_concept_block())