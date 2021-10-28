import ccxt
from datetime import datetime
from slacker import Slacker

minAmt = 0.09
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


def getBalance():
    balance = binance.fetch_balance(params={"type": "future"})
    return str(balance['USDT'])


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
        print("[물타기 스킵] 현재 봉에 구매 이력 있어서")
        return False
    elif nowCandle[4] > getEntryPrice():
        print("[물타기 스킵] 현재 가격이 평균 가격보다 비싸서")
        return False
    else:
        if prevCandle[4] - prevCandle[1] < -3:
            print("WATER")
            return True
        else:
            print("[물타기 스킵] 이번 봉은 음봉이 아니어서")
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
        amount=minAmt,
    )
    price = order["price"]
    nowPositionAmt = getPositionAmt()
    print("구매시 가격 : ", price, ", nowPositionAmt : ", nowPositionAmt)
    updateTime = order["info"]["updateTime"]
    slackBuy(price, "")
    writeRecord(updateTime)
    targetPrice = round(float(price) * 1.0033, 2)
    createLimitSell(targetPrice, nowPositionAmt)


def water():
    order = binance.create_market_buy_order(
        symbol="ETH/USDT",
        amount=minAmt,
    )
    price = order["price"]
    updateTime = order["info"]["updateTime"]
    writeRecord(updateTime)
    binance.cancel_all_orders(symbol="ETH/USDT")
    nowPositionAmt = getPositionAmt()
    slackBuy(price, "water " + str(nowPositionAmt))
    sellAmount = 0
    if nowPositionAmt > minAmt * 2:
        print("처음 의도된 파는 양 : ", round(nowPositionAmt - minAmt * 2, 2))
        sellAmount = createLimitSell(round(getEntryPrice() * 1.0011, 2), round(nowPositionAmt - minAmt * 2, 2))
        print(round(getEntryPrice() * 1.0011, 2), "가격으로 ", sellAmount, "만큼 팔기")
    createLimitSell(round(getEntryPrice() * 1.0022, 2), round(nowPositionAmt - sellAmount, 3))
    print(round(getEntryPrice() * 1.0022, 2), "가격으로 ", round(nowPositionAmt - sellAmount, 3), "만큼 팔기")


def checkAndBuy(term):
    if term == 5:
        if checkIfGoodToBuy():
            print("사기 좋군  ", datetime.now())
            buy()
    elif term == 15:
        if checkIfGoodToWater():
            water()
