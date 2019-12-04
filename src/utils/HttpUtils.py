from flask import jsonify

def success(data = {}):
    return jsonify({
        "code": "200",
        "data": data
    })


def fail(message, code='400'):
    return jsonify({
        "code": code,
        "message": message
    })