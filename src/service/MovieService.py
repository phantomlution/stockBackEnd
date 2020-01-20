'''

'''

from src.service.DatabaseService import DatabaseService
import bson
from src.utils.lodash import lodash

mongo = DatabaseService.get_mongo_instance()

movie_document = mongo.stock.movie_series
movie_comment_document = mongo.stock.movie_comment


class MovieService:

    @staticmethod
    def get_movie_list():
        result = []
        for item in movie_document.find():
            item['_id'] = str(item['_id'])
            result.append(item)

        return result

    @staticmethod
    def get_movie(_id):
        return movie_document.find_one({ '_id': bson.ObjectId(_id)})

    @staticmethod
    def add_comment(model):
        movie_id = model['movieId']
        movie = MovieService.get_movie(movie_id)
        if movie is None:
            raise Exception('找不到movie')

        # 匹配 season 和 episode
        season = model['season']
        episode = model['episode']

        episode_item = lodash.find(movie['series'], lambda item: item['season'] == season and episode in item['episode'])
        if episode_item is None:
            raise Exception('season, episode 不匹配')

        db_model = {
            'movie_id': movie_id,
            'season': season,
            'episode': episode,
            'time': model['time'],
            'content': model['content']
        }
        movie_comment_document.insert(db_model)
        return


if __name__ == '__main__':
    result = MovieService.get_movie_list()
    print(result)