from flask import Flask
from src.script.worker.WorkScheduler import start_schedule
from src.routes.Stock import stock_api
from src.routes.Data import data_api
from src.routes.StockPool import stock_pool_api
from src.routes.Notification import notification_api
from src.routes.CustomEvent import custom_event_api
from src.routes.Analyze import analyze_api
from src.routes.News import news_api
from src.routes.Live import live_api
from src.routes.Chess import chess_api
from src.routes.EventCalendar import event_calendar_api
from src.routes.Movie import movie_api

app = Flask(__name__)

app.register_blueprint(stock_api)
app.register_blueprint(data_api)
app.register_blueprint(stock_pool_api)
app.register_blueprint(notification_api)
app.register_blueprint(custom_event_api)
app.register_blueprint(analyze_api)
app.register_blueprint(news_api)
app.register_blueprint(live_api)
app.register_blueprint(chess_api)
app.register_blueprint(event_calendar_api)
app.register_blueprint(movie_api)

app.config['SECRET_KEY'] = 'secret!'

if __name__ == '__main__':
    # 启动任务调度
    start_schedule()
    port = 5001
    print('server run at:' + str(port))
    app.run(port=port)