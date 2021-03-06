import ccxt
from datetime import datetime
from slacker import Slacker
import time
import json

minAmt = 0.05  # 621 * 3 / 5000 / 10
recordFilePath = "record.txt"


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
    position = [x for x in balance['info']['positions'] if x['symbol'] == "ETHUSDT"][0]
    if float(position["positionAmt"]) > 0:
        return True
    else:
        return False


def slackPositionClosed():
    slack.chat.post_message('#autostock', 'position closed,' + getBalance())


def slackBuy(price, message):
    slack.chat.post_message("#autostock", "buy, " + str(price) + " (" + message + ")")


def slackNoMoney():
    slack.chat.post_message('#autostock', 'not enough money, ' + str(getBalanceFree()))


def slackMessage(message):
    slack.chat.post_message('#autostock', message)


def getBalance():
    balance = binance.fetch_balance()
    return str(balance['USDT'])


def getBalanceFree():
    balance = binance.fetch_balance()
    return balance['USDT']["free"]


def getNowPrice():
    ticker = binance.fetch_ticker('ETH/USDT')
    return ticker['close']


def showDateTime(dateTime):
    return datetime.fromtimestamp(dateTime / 1000).strftime('%Y-%m-%d %H:%M:%S')


def getEntryPrice():
    balance = binance.fetch_balance()
    return float([x for x in balance['info']['positions'] if x['symbol'] == "ETHUSDT"][0]["entryPrice"])


def getPositionAmt():
    balance = binance.fetch_balance()
    return float([x for x in balance['info']['positions'] if x['symbol'] == "ETHUSDT"][0]["positionAmt"])


def checkIfGoodToWater():
    eth15m = binance.fetch_ohlcv(
        symbol="ETH/USDT",
        timeframe='15m',
        since=None,
        limit=2)
    with open(recordFilePath) as f:
        lines = f.readlines()
    prevCandle = eth15m[0]
    nowCandle = eth15m[1]
    if int(lines[-1]) > nowCandle[0]:
        print("[????????? ??????] ?????? ?????? ?????? ?????? ?????????")
        return False
    elif nowCandle[4] > getEntryPrice():
        print("[????????? ??????] ?????? ????????? ?????? ???????????? ?????????")
        return False
    else:
        if prevCandle[4] - prevCandle[1] < -3:
            print("WATER")
            return True
        else:
            print("[????????? ??????] ?????? ?????? ????????? ????????????")
            return False


def checkIfGoodToBuy():
    eth5m = binance.fetch_ohlcv(
        symbol="ETH/USDT",
        timeframe='5m',
        since=None,
        limit=12)
    candleL = []
    for e in eth5m[:-1]:
        candle = e[4] - e[1]
        if candle > 3:
            candleL.append("white")
        elif candle < -3:
            candleL.append("black")
        else:
            candleL.append("")
    if len(candleL) < 3:
        return False
    goodStack = 0
    for i in range(len(candleL) - 1, -1, -1):
        if candleL[i] == "white":
            return False
        elif candleL[i] == "black":
            goodStack += 1
        elif candleL[i] == "" and goodStack >= 3:
            return True
        if goodStack >= 4:
            return True
    return False


def getTodayDate():
    now = datetime.now()
    nowDate = now.strftime('%Y%m%d')
    return nowDate


def writeRecord(updateTime):
    with open(recordFilePath, "w") as f:
        f.write(updateTime)


def createLimitSell(price, amount):
    order = binance.create_limit_sell_order(
        symbol='ETH/USDT',
        amount=amount,
        price=price
    )
    return order["amount"]


def buy():
    order = binance.create_market_buy_order(
        symbol="ETH/USDT",
        amount=round(minAmt * 2, 2),
    )
    price = order["price"]
    nowPositionAmt = getPositionAmt()
    print("????????? ?????? : ", price, ", nowPositionAmt : ", nowPositionAmt)
    updateTime = order["info"]["updateTime"]
    slackBuy(price, "")
    writeRecord(updateTime)
    targetPrice = round(float(price) * 1.0033, 2)
    createLimitSell(targetPrice, nowPositionAmt)


def water():
    if getBalanceFree() < minAmt * getNowPrice() * 1.2:
        order = binance.create_order(
            symbol="ETH/USDT",
            type='stop_loss_limit',
            params={'stopPrice': getEntryPrice() * 0.9}
        )
        slackNoMoney()
        slackMessage("stop loss price : " + str(getEntryPrice() * 0.9) + ", order result : " + json.dumps(order))
        return
    order = binance.create_market_buy_order(
        symbol="ETH/USDT",
        amount=minAmt,
    )
    price = order["price"]
    updateTime = order["info"]["updateTime"]
    writeRecord(updateTime)
    binance.cancel_all_orders(symbol="ETH/USDT")
    time.sleep(3)
    nowPositionAmt = getPositionAmt()
    slackBuy(price, "water " + str(nowPositionAmt))
    sellAmount = 0
    if nowPositionAmt > minAmt * 2:
        print("?????? ????????? ?????? ??? : ", round(nowPositionAmt - minAmt * 2, 2))
        sellAmount = createLimitSell(round(getEntryPrice() * 1.0011, 2), round(nowPositionAmt - minAmt * 2, 2))
        print(round(getEntryPrice() * 1.0011, 2), "???????????? ", sellAmount, "?????? ??????")
    createLimitSell(round(getEntryPrice() * 1.0022, 2), round(nowPositionAmt - sellAmount, 3))
    print(round(getEntryPrice() * 1.0022, 2), "???????????? ", round(nowPositionAmt - sellAmount, 3), "?????? ??????")


def checkAndBuy(term):
    if term == 5:
        if checkIfGoodToBuy():
            print("?????? ??????  ", datetime.now())
            buy()
    elif term == 15:
        if checkIfGoodToWater():
            water()
