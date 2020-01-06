'''
    新闻
'''

from flask import Blueprint, request
from src.service.NewsService import NewsService
from src.utils.decorator import flask_response
news_api = Blueprint('news_api', __name__, url_prefix='/news')


@news_api.route('/page/read')
@flask_response
def get_read_news_page():
    query = {
        "has_read": True
    }
    return NewsService.paginate(query, limit=50)


@news_api.route('/page/unread')
@flask_response
def get_unread_news_page():
    query = {
        "has_read": False
    }
    return NewsService.paginate(query)


@news_api.route('/mark/read', methods=['PUT'])
@flask_response
def update_news_read_status():
    _id = request.args.get('id')
    NewsService.mark_read(_id)
    return {}


@news_api.route('/mark/subscribe', methods=['PUT'])
@flask_response
def update_news_subscribe():
    _id = request.args.get('id')
    subscribe = int(request.args.get('subscribe'))
    NewsService.mark_subscribe(_id, subscribe)
    return {}
