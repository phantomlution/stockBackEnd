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

@app.route('/book/list', methods=['GET'])
def book_list():
    return jsonify(list(mongo.geekbang.directory.find({}, { "_id": 0})))

@app.route('/book/chapter/list', methods=['GET'])
def base():
    book_id = request.args.get('id')
    return jsonify(list(mongo.geekbang.column.find({ "cid": int(book_id)}, { "_id": 0, })))

if __name__ == '__main__':
    app.run(port=9999)
