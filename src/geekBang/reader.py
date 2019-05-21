from flask import Flask, request, jsonify, render_template
from src.service.stockService import StockService
from flask_cors import CORS

mongo = StockService.getMongoInstance()

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    with open('./templates/reader.html', 'r') as file:
        data = file.read()
    return data

@app.route('/book/list', methods=['GET'])
def book_list():
    return jsonify(list(mongo.geekbang.directory.find({}, { "_id": 0})))

@app.route('/book/chapter/list', methods=['GET'])
def base():
    book_id = request.args.get('id')
    return jsonify(list(mongo.geekbang.column.find({ "cid": int(book_id)}, { "_id": 0, })))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=9999, threaded=True)
