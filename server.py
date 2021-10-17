from flask import Flask
import utils
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)


def check5Min():
    global positionExist
    if positionExist and not utils.checkPositionExist():
        positionExist = False
        utils.slackPositionClosed()
    return 5


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


utils.init()
utils.slackPositionClosed()
positionExist = utils.checkPositionExist()
sched = BackgroundScheduler(daemon=True)
sched.add_job(check5Min, 'cron', minute="*/5", second="5")
sched.start()
