from flask import Flask, request, jsonify
from src.service.StockService import StockService
from src.service.BondService import BondService
from src.script.job.StockTradeDataJob import StockTradeDataJob
from src.script.job.StockNoticeJob import StockNoticeJob
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
# TODO
loadStockNotice = getattr(StockNoticeJob(), 'load_stock_notice')

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

@app.route('/financial/bond/list', methods=['GET'])
def get_bond_list():
    return success(BondService.get_stock_bond_list())

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