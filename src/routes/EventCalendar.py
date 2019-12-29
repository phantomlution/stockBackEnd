'''
    事件日历
'''

from flask import Blueprint, request
from src.service.EventCalendarService import EventCalendarService
from src.utils.decorator import flask_response
event_calendar_api = Blueprint('event_calendar_api', __name__, url_prefix='/event/calendar')


@event_calendar_api.route('/', methods=['POST'])
@flask_response
def add_custom_event_item():
    model = request.get_json()
    return EventCalendarService.add_item(model)


@event_calendar_api.route('/', methods=['GET'])
@flask_response
def get_custom_event_list():
    return EventCalendarService.get_item_list()
