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
        print("")
    elif positionExist and utils.checkPositionExist():
        utils.checkAndBuy(15)
    elif not positionExist:
        utils.checkAndBuy(5)
        positionExist = utils.checkPositionExist()


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


utils.init()
positionExist = utils.checkPositionExist()
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(check5Min, 'cron', minute="*/5", second="5")
scheduler.start()
