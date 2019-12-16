'''
    7*24资讯直播
'''
from flask import Blueprint, request
from src.service.DataService import DataService
from src.utils.decorator import flask_response
live_api = Blueprint('live_api', __name__, url_prefix='/live')


@live_api.route('/fx')
@flask_response
def get_fx_live():
    date_str = request.args.get('date')
    return DataService.get_fx_live(date_str)