from flask import Flask
import utils
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)


def check5Min():
    print("ohohohoh")
    return 5


sched = BackgroundScheduler(daemon=True)
sched.add_job(check5Min, 'cron', minute="*/5", second="5")
sched.start()


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
