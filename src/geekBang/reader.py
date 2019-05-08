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
    collection = request.args.get('collection')
    columnId = request.args.get('columnId')

    return jsonify(mongo.geekbang[collection].find({ "column_id": columnId }))

if __name__ == '__main__':
    app.run(port=9999)
