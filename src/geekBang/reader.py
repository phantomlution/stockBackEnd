from flask import Flask, request, jsonify, render_template
from src.service.stockService import StockService
from flask_cors import CORS
import json

mongo = StockService.getMongoInstance()

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    return render_template('reader.html')

@app.route('/column/list', methods=['POST'])
def base():
    params = request.get_json()

@app.route('/column/detail', methods=['GET'])
def detail():
    id = request.args.get('id')
    cid = request.args.get('cid')
    return jsonify(mongo.geekbang.column.find_one({ "cid": int(cid), "id": int(id) }, { "_id": 0 }))

if __name__ == '__main__':
    app.run(port=9999)
