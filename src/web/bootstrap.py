from flask import Flask, request, jsonify
from src.service.stockService import StockService

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
    params = request.form
    return success(mongo.stock.history_2019_03_12.find_one(params, { "_id": 0 }))

if __name__ == '__main__':
    app.run(port=5001)
