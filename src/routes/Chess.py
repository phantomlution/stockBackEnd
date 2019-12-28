'''
    市场预测以及复盘
'''

from flask import Blueprint, request
from src.utils.decorator import flask_response
from src.service.ChessService import ChessService

chess_api = Blueprint('chess_api', __name__, url_prefix='/chess')


@chess_api.route('/')
@flask_response
def get_chess_item():
    date_list = request.args.get('dateList').split(',')
    result = []
    for _date in date_list:
        result.append(ChessService.get_item(_date))
    return result


@chess_api.route('/', methods=['PUT'])
@flask_response
def update_chess_item():
    model = request.get_json()
    _date = model['date']
    field = model['field']
    content = model['content']

    if field == 'predict':
        return ChessService.update_predict(_date, content)
    elif field == 'replay':
        return ChessService.update_replay(_date, content)
    else:
        raise Exception('参数错误')




