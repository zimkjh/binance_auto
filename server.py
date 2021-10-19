from flask import Flask
import utils
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)


def check5Min():
    global positionExist
    if positionExist and not utils.checkPositionExist():
        print("포지션 종료")
        positionExist = False
        utils.slackPositionClosed()
    elif positionExist and utils.checkPositionExist():
        print("기존에 사둔게 있음  ")
        utils.checkAndBuy(15)
    elif not positionExist:
        print("새로살게 있나??? ")
        utils.checkAndBuy(5)
    print("")


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


utils.init()
utils.slackPositionClosed()
positionExist = utils.checkPositionExist()
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(check5Min, 'cron', minute="*/5", second="5")
scheduler.start()
