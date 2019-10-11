from flask import Flask, request, jsonify
from src.service.StockService import StockService
from src.script.job.StockTradeDataJob import StockTradeDataJob
from src.assets.DataProvider import DataProvider
from src.service.DataService import DataService
from flask_socketio import SocketIO, emit
from bson import json_util
from src.script.extractor.event import extractData
from src.script.extractor.centualBank import extractAllCentualBank
import json
from src.service.HtmlService import get_parsed_href_html


mongo = StockService.getMongoInstance()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, threaded=True)

# TODO
calculateBiKiller = getattr(StockTradeDataJob(), 'load_stock_data')
# TODO
getTotalStockList = getattr(DataProvider(), 'get_stock_list')

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

def getStockDetail(params):
    # 最后一天的数据不准确
    return mongo.stock.history.find_one(params, {"_id": 0})

@app.route('/stock/index', methods=['GET'])
def getMarketIndex():
    # 获取开市时间列表
    code = request.args.get('code')
    count = request.args.get('count')
    return success(calculateBiKiller(code, count))

@app.route('/stock/base', methods=['GET'])
def base():
    code = request.args.get('code')
    return success(mongo.stock.base.find_one({ "symbol": code }, { "_id": 0 }))

@app.route('/stock/list')
def stockList():
    base_list = list(mongo.stock.base.find({ "type": 11 }, {"_id": 0}))

    return success({
        # "idList": list(mongo.stock.base.find({ "type": 11, "status": 1 }, { "_id": 0 })),
        "idList": base_list,
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


# 获取预披露的公告信息
@app.route('/stock/pool/prerelease/calendar', methods=['GET'])
def get_stock_pool_pre_release_calendar():
    stock_list = mongo.stock.stock_pool.find()
    result = []
    for stock in stock_list:
        result.append({
            "code": stock['code'],
            "name": stock['name'],
            "list": StockService.load_pre_release_notice(stock['code'])
        })

    return success(result)

@app.route('/stock/notice')
def getNotice():
    code = request.args.get('code')
    response = StockService.load_stock_notice(code)
    return success(response)

@app.route('/stock/notice/change')
def get_stock_notice_change():
    code = request.args.get('code')
    return success(StockService.get_stock_notice_change(code))


@app.route('/stock/pool', methods=['GET'])
def getStockPool():
    return success(StockService.get_stock_pool())


@app.route('/stock/pool', methods=['POST'])
def addToStockPool():
    item = request.get_json()
    StockService.add_stock_pool(item)
    return success()


@app.route('/stock/pool', methods=['DELETE'])
def removeFromStockPool():
    code = request.args.get('code')
    return success(StockService.remove_stock_pool(code))


@app.route('/stock/theme', methods=['GET'])
def getStockThemeList():
    result = mongo.stock.theme.find({}, { "_id": 0 })
    return success(list(result))

@app.route('/stock/detail/pledge')
def get_stock_pledge():
    code = request.args.get('code')
    return success(StockService.get_pledge_rate(code))

def socketSuccess(data):
    return json.dumps({
        "code": 200,
        "data": data
    }, default=json_util.default)


@app.route('/product/farm', methods=['GET'])
def searchFarmProductIndex():
    goodsId = request.args.get('goodsId')
    return success(DataService.get_farm_product_index(goodsId))


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


@app.route('/financial/product', methods=['GET'])
def get_financial_product():
    key = request.args.get('key')
    result = mongo.stock.temp.find_one({ "key": key })
    return success(list(result['list']))


@app.route('/financial/shibor', methods=['GET'])
def get_financial_shibor():
    start = request.args.get('start')
    end = request.args.get('end')
    return success(DataService.get_shibor_data(start, end))


@app.route('/financial/estate/date/list', methods=['GET'])
def get_estate_date_list():
    sync_document = mongo.stock.sync
    result = []
    date_list = sync_document.find({"key": { "$regex": "^estate"}, "done": True })
    for date in date_list:
        result.append( date['key'].split('_')[1])

    return success(result)


@app.route('/financial/estate', methods=['GET'])
def get_estate_data():
    date = request.args.get('date')
    estate_document = mongo.stock.estate

    return success(list(estate_document.find({ "date": date }, { "_id": 0 })))

@app.route('/financial/huitong/index')
def get_huitong_index_list():
    huitong_document = mongo.stock.huitong

    return success(list(huitong_document.find({}, { "_id": 0 })))

@app.route('/redirect', methods=['GET'])
def redirect():
    url = request.args.get('url')

    return get_parsed_href_html(url)


@socketio.on('request')
def test_message(message):
    key = message['key']
    params = message['params']
    request_id = message['requestId']
    if key == 'stockDetail':
        emit('response_' + request_id, socketSuccess(getStockDetail(params)))

if __name__ == '__main__':
    # app.run(port=5001)
    port = 5001
    print('server run at:' + str(port))
    socketio.run(app, port=port)