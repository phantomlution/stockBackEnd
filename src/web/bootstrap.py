from flask import Flask, request, jsonify
from src.service.stockService import StockService
from src.script.byKiller import calculateBiKiller, getTotalStockList
from flask_socketio import SocketIO, emit
from bson import json_util
import json
import zlib

mongo = StockService.getMongoInstance()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

def success(data):
    return jsonify({
        "code": "200",
        "data": data
    })

@app.route('/')
def hello():
    name = request.args.get('name', 'World')
    return f'Hello, {name}'

@app.route('/stock/detail', methods=['POST'])
def detail():
    params = request.get_json()
    return success(getStockDetail(params))


def getStockDetail(params):
    # 最后一天的数据不准确
    #return mongo.stock.history.find_one(params, {"_id": 0})
    return calculateBiKiller(params.get('code'), params.get('count'))

@app.route('/stock/base', methods=['POST'])
def base():
    params = request.get_json()
    return success(mongo.stock.base.find_one(params, { "_id": 0 }))

@app.route('/stock/list')
def stockList():
    return success({
        "idList": list(mongo.stock.base.find({ "type": 11, "status": 1 }, { "_id": 0 })),
        "nameList": getTotalStockList()
    })

def socketSuccess(data):
    return json.dumps({
        "code": 200,
        "data": data
    }, default=json_util.default)



@socketio.on('request')
def test_message(message):
    key = message['key']
    params = message['params']
    requestId = message['requestId']
    if key == 'stockDetail':
        emit('response_' + requestId, socketSuccess(getStockDetail(params)))

if __name__ == '__main__':
    # app.run(port=5001)
    socketio.run(app, port=5001)