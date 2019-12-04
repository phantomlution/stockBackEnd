from functools import wraps
from flask import jsonify


def flask_response(func):
    @wraps(func)
    def response(*args, **kwargs):
        try:
            data = func(*args, **kwargs)
            return jsonify({
                "code": "200",
                "data": data
            })
        except Exception as e:
            return jsonify({
                "code": '400',
                "message": e
            })
    return response
