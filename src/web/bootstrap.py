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
from src.service.HtmlService import get_parsed_href_html, get_response


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


def fail(message, code='400'):
    return jsonify({
        "code": code,
        "message": message
    })


@app.route('/')
def hello():
    name = request.args.get('name', 'World')
    return f'Hello, {name}'


@app.route('/stock/detail', methods=['GET'])
def detail():
    code = request.args.get('code')
    return success({
        "base": StockService.get_stock_base(code),
        "data": get_stock_detail({ "code": code })
    })


def get_stock_detail(params):
    # 最后一天的数据不准确
    return mongo.stock.history.find_one(params, {"_id": 0})


@app.route('/stock/index', methods=['GET'])
def get_market_index():
    # 获取开市时间列表
    code = request.args.get('code')
    count = request.args.get('count')
    return success(calculateBiKiller(code, count))


@app.route('/stock/base', methods=['GET'])
def get_stock_base():
    code = request.args.get('code')
    return success(mongo.stock.base.find_one({ "symbol": code }, { "_id": 0 }))


@app.route('/stock/list')
def get_stock_list():
    return success(DataProvider().get_stock_list())


@app.route('/stock/capital/flow')
def get_stock_capital_flow():
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
def get_notice():
    code = request.args.get('code')
    response = StockService.load_stock_notice(code)
    return success(response)


@app.route('/stock/notice/change')
def get_stock_notice_change():
    code = request.args.get('code')
    return success(StockService.get_stock_notice_change(code))


@app.route('/stock/pool', methods=['GET'])
def get_stock_pool():
    return success(StockService.get_stock_pool())


@app.route('/stock/pool', methods=['POST'])
def add_to_stock_pool():
    item = request.get_json()
    code = item['code']
    if StockService.stock_pool_exist(code):
        return fail('该代码已存在')
    StockService.add_stock_pool(item)
    return success()


@app.route('/stock/pool', methods=['DELETE'])
def remove_from_stock_pool():
    code = request.args.get('code')
    return success(StockService.remove_stock_pool(code))


@app.route('/stock/theme', methods=['GET'])
def get_stock_theme_list():
    result = mongo.stock.theme.find({}, { "_id": 0 })
    return success(list(result))


@app.route('/stock/theme/market', methods=['GET'])
def get_stock_theme_market():
    theme_market_list = mongo.stock.theme_market.find({}, { "_id": 0 })
    return success(list(theme_market_list))


# 查询某一个十大股东，目前能查到的所有持股信息
@app.route('/stock/share/all', methods=['GET'])
def get_all_company_stock_share():
    url = request.args.get('url')
    return success(StockService.get_all_stock_share_company(url))

@app.route('/stock/detail/pledge')
def get_stock_pledge():
    code = request.args.get('code')
    return success(StockService.get_pledge_rate(code))


@app.route('/stock/detail/biding')
def get_stock_biding():
    code = request.args.get('code')
    return success(StockService.get_stock_biding(code))


def socket_success(data):
    return json.dumps({
        "code": 200,
        "data": data
    }, default=json_util.default)


@app.route('/product/farm', methods=['GET'])
def search_farm_product_index():
    goods_id = request.args.get('goodsId')
    return success(DataService.get_farm_product_index(goods_id))


@app.route('/financial/information', methods=['GET'])
def get_financial_information():
    date = request.args.get('date')
    data = extractData(date)

    return success({
        "date": date,
        "data": data
    })


@app.route('/financial/centralBank', methods=['GET'])
def get_central_bank_financial_info():
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

@app.route('/data/stat/country', methods=['GET'])
def get_country_stat():
    code = request.args.get('code')
    return success(DataService.get_stat_info(code))

@app.route('/financial/huitong/index')
def get_huitong_index_list():
    huitong_document = mongo.stock.huitong

    return success(list(huitong_document.find({}, { "_id": 0 })))


@app.route('/redirect', methods=['GET'])
def redirect():
    url = request.args.get('url')
    response = get_response(url)

    parsed_html = get_parsed_href_html(url, response)

    # if 'cn.investing.com' in url:
    #     parsed_html = parsed_html.replace('//sbcharts.investing.com', '/api/redirect?url=' + 'https://sbcharts.investing.com')
    return parsed_html


@socketio.on('request')
def test_message(message):
    key = message['key']
    params = message['params']
    request_id = message['requestId']
    if key == 'stockDetail':
        emit('response_' + request_id, socket_success(get_stock_detail(params)))


if __name__ == '__main__':
    # app.run(port=5001)
    port = 5001
    print('server run at:' + str(port))
    socketio.run(app, port=port)