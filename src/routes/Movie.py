'''
    电影分析
'''

from flask import Blueprint, request
from src.utils.decorator import flask_response
from src.service.MovieService import MovieService
movie_api = Blueprint('movie_api', __name__, url_prefix='/movie')


@movie_api.route('/')
@flask_response
def get_movie_list():
    return MovieService.get_movie_list()


@movie_api.route('/comment', methods=['POST'])
@flask_response
def add_movie_comment():
    model = request.get_json()
    return MovieService.add_comment(model)
