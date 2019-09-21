from flask import Flask, request, jsonify
from src.service.stockService import StockService
from src.script.byKiller import calculateBiKiller, getTotalStockList, loadStockNotice, getFarmProductIndex
from flask_socketio import SocketIO, emit
from bson import json_util
from src.script.extractor.event import extractData
from src.script.extractor.centualBank import extractAllCentualBank
import json

mongo = StockService.getMongoInstance()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, threaded=True)

def success(data = {}):
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

history_cache = {}

def getStockDetail(params):
    # 最后一天的数据不准确
    return mongo.stock.history.find_one(params, {"_id": 0})

@app.route('/stock/index', methods=['GET'])
def getMarketIndex():
    # 获取开市时间列表
    code = request.args.get('code')
    count = request.args.get('count')
    return success(calculateBiKiller(code, count))

@app.route('/stock/base', methods=['POST'])
def base():
    params = request.get_json()
    return success(mongo.stock.base.find_one(params, { "_id": 0 }))

@app.route('/stock/list')
def stockList():
    return success({
        # "idList": list(mongo.stock.base.find({ "type": 11, "status": 1 }, { "_id": 0 })),
        "idList": list(mongo.stock.base.find({ "type": 11 }, {"_id": 0})),
        "nameList": getTotalStockList()
    })

@app.route('/stock/capital/flow')
def capitalFlow():
    date = request.args.get('date')
    return success(mongo.stock.capitalFlow.find_one({ "date": date }, { "_id": 0 }))

@app.route('/stock/capital/hotMoney')
def hotMoney():
    date = request.args.get('date')
    return success(mongo.stock.hotMoney.find_one({ "date": date }, { "_id": 0 }))

@app.route('/stock/notice')
def getNotice():
    code = request.args.get('code')
    response = loadStockNotice(code)
    return success(response)

@app.route('/stock/pool', methods=['GET'])
def getStockPool():
    return success(mongo.stock.sense.find_one({ "code": 'pool' }, { "_id": 0 }))

@app.route('/stock/pool', methods=['PUT'])
def updateStockPool():
    item = request.get_json()
    model = {
        "code": "pool",
        "list": item
    }
    mongo.stock.sense.update({"code": "pool"}, model, True)
    return success()

@app.route('/stock/notice/search', methods=['GET'])
def getStockNoticeSearch():
    keyword = request.args.get('keyword')
    result = mongo.stock.notice.find({ "data.NOTICETITLE": { '$regex': r'' + keyword } }, { '_id': 0 })
    return success(list(result))

@app.route('/stock/theme', methods=['GET'])
def getStockThemeList():
    result = mongo.stock.theme.find({}, { "_id": 0 })
    return success(list(result))

def socketSuccess(data):
    return json.dumps({
        "code": 200,
        "data": data
    }, default=json_util.default)

@app.route('/product/farm', methods=['GET'])
def searchFarmProductIndex():
    goodsId = request.args.get('goodsId')
    return success(getFarmProductIndex(goodsId))

@app.route('/financial/information', methods=['GET'])
def getFinancialInformation():
    date = request.args.get('date')
    data = extractData(date)

    return success({
        "date": date,
        "data": data
    })

@app.route('/financial/centralBank', methods=['GET'])
def getCentralBankFinancialInfo():

    return success(extractAllCentualBank())


@socketio.on('request')
def test_message(message):
    key = message['key']
    params = message['params']
    requestId = message['requestId']
    if key == 'stockDetail':
        emit('response_' + requestId, socketSuccess(getStockDetail(params)))

if __name__ == '__main__':
    # app.run(port=5001)
    port = 5001
    print('server run at:' + str(port))
    socketio.run(app, port=port)