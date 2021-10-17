import ccxt
import pprint
from datetime import datetime
from slacker import Slacker


def init():
    global slack, binance
    with open("apiKey_ham.txt") as f:
        lines = f.readlines()
        apiKey = lines[0].strip()
        secret = lines[1].strip()
        slackToken = lines[2].strip()
    slack = Slacker(slackToken)
    binance = ccxt.binance({
        'apiKey': apiKey,
        'secret': secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future'
        }
    })


def checkPositionExist():
    balance = binance.fetch_balance()
    positions = [x for x in balance['info']['positions'] if x['symbol'] == "ETHUSDT"]
    if len(positions) > 0:
        return True
    else:
        return False


def slackPositionClosed():
    slack.chat.post_message('#autostock', 'position closed,' + getBalance())


def getBalance():
    balance = binance.fetch_balance(params={"type": "future"})
    return str(balance['USDT'])
