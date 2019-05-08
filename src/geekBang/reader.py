from flask import Flask, request, jsonify, render_template
from src.service.stockService import StockService
import json

mongo = StockService.getMongoInstance()

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('reader.html')

@app.route('/stock/base', methods=['POST'])
def base():
    params = request.get_json()


if __name__ == '__main__':
    app.run(port=9999)
