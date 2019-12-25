'''
    自定义事件
'''

from flask import Blueprint, request
from src.service.CustomEventService import CustomEventService
from src.utils.decorator import flask_response
custom_event_api = Blueprint('custom_event_api', __name__, url_prefix='/event/custom')


@custom_event_api.route('/list', methods=['GET'])
@flask_response
def get_custom_event_list():
    return CustomEventService.get_custom_event_list()


@custom_event_api.route('', methods=['GET'])
@flask_response
def get_custom_event():
    event_id = request.args.get('event_id')
    return CustomEventService.get_custom_event(event_id)


@custom_event_api.route('', methods=['PUT'])
@flask_response
def update_custom_event():
    model = request.get_json()
    CustomEventService.update_custom_event(model)
    return {}


@custom_event_api.route('/save', methods=['POST'])
@flask_response
def save_custom_event():
    request_json = request.get_json()
    event_name = str.strip(request_json['name'])
    if len(event_name) == 0:
        raise Exception('请填写事件名')

    return CustomEventService.save_event(event_name)


@custom_event_api.route('/item/list', methods=['GET'])
@flask_response
def get_custom_event_item_list():
    event_id = request.args.get('event_id')
    return CustomEventService.get_custom_event_item_list(event_id)


@custom_event_api.route('/item/save', methods=['POST'])
@flask_response
def save_custom_event_item():
    item = request.get_json()

    event_type = item['type']
    if event_type == 'stock' and len(item['stockCode']) != 8:
        raise Exception('股票代码错误')
    elif event_type == 'custom' and len(item['eventId']) == 0:
        raise Exception('未关联事件')

    CustomEventService.save_event_item(item)
    return {}