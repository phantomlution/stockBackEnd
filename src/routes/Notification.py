'''
    通知
'''

from flask import Blueprint, request
from src.service.NotificationService import NotificationService
from src.utils.decorator import flask_response
notification_api = Blueprint('notification_api', __name__, url_prefix='/notification')


# 获取所有的未读通知
@notification_api.route('/list')
@flask_response
def get_unread_notification():
    result = []
    notification_list = NotificationService.get_unread_notification()
    for notification in notification_list:
        notification['_id'] = str(notification['_id'])
        result.append(notification)
    return result


@notification_api.route('/read', methods=['PUT'])
@flask_response
def update_notification_read_status():
    _id = request.args.get('id')
    return NotificationService.update_read_status(_id)