from flask import Flask, request, jsonify
from src.service.stockService import StockService
from src.script.byKiller import calculateBiKiller, getTotalStockList
import json

mongo = StockService.getMongoInstance()

app = Flask(__name__)

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
    print(params)
    # 最后一天的数据不准确
    #return success(mongo.stock.history_2019_03_12.find_one(params, { "_id": 0 }))
    return success(calculateBiKiller(params.get('code'), 600))

@app.route('/stock/base', methods=['POST'])
def base():
    params = request.get_json()
    return success(mongo.stock.base.find_one(params, { "_id": 0 }))

@app.route('/stock/list')
def stockList():
    return success({
        "idList": list(mongo.stock.base.find({ "type": 11 }, { "_id": 0 })),
        "nameList": getTotalStockList()
    })


if __name__ == '__main__':
    app.run(port=5001)
