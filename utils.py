import ccxt
from datetime import datetime
from slacker import Slacker

minAmt = 0.008


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
    fileName = "record/" + getTodayDate() + ".txt"
    with open(fileName) as f:
        lines = f.readlines()
    prevCandle = eth15m[0]
    nowCandle = eth15m[1]
    if int(lines[-1].split()[0]) > nowCandle[0]:
        print("현재 봉에 구매 이력 있어서 물타기 스킵")
        return False
    elif nowCandle[4] > getEntryPrice():
        print("현재 가격이 평균 가격보다 비싸서 물타기 스킵  ")
        return False
    else:
        if prevCandle[4] - prevCandle[1] < -3:
            print("물타기 하기~")
            return True
        else:
            print("이번 봉은 음봉이 아니라 물타기 스킵")
            return False


def checkIfGoodToBuy():
    eth5m = binance.fetch_ohlcv(
        symbol="ETH/USDT",
        timeframe='5m',
        since=None,
        limit=10)
    candleL = []
    for e in eth5m[:-1]:
        candle = e[4] - e[1]
        if candle > 3:
            candleL.append("white")
        elif candle < -3:
            candleL.append("black")
        else:
            candleL.append("")
    print(candleL)
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


def writeRecord(updateTime, avgPrice):
    fileName = "record/" + getTodayDate() + ".txt"
    try:
        with open(fileName) as f:
            lines = f.readlines()
    except:
        f = open(fileName, "w")
        f.close()
        lines = []
    lines.append(str(updateTime) + " " + str(avgPrice) + "\n")
    with open(fileName, "w") as f:
        for line in lines:
            f.write(line)


def createLimitSell(price, amount):
    binance.create_limit_sell_order(
        symbol='ETH/USDT',
        amount=amount,
        price=price
    )


def buy():
    order = binance.create_market_buy_order(
        symbol="ETH/USDT",
        amount=minAmt,
    )
    price = order["price"]
    print("구매시 가격 : ", price)
    updateTime = order["info"]["updateTime"]
    slackBuy(price, "")
    writeRecord(updateTime, price)
    targetPrice = round(float(price) * 1.0033, 2)
    createLimitSell(targetPrice, minAmt)


def water():
    order = binance.create_market_buy_order(
        symbol="ETH/USDT",
        amount=minAmt,
    )
    price = order["price"]
    print("물 탔을때 가격 : ", price)
    updateTime = order["info"]["updateTime"]
    slackBuy(price, "water")
    writeRecord(updateTime, price)
    binance.cancel_all_orders(symbol="ETH/USDT")
    nowPositionAmt = getPositionAmt()
    if nowPositionAmt > minAmt * 2:
        createLimitSell(round(getEntryPrice() * 1.0011, 2), nowPositionAmt - minAmt * 2)
    createLimitSell(round(getEntryPrice() * 1.0022, 2), minAmt * 2)
    print(round(getEntryPrice() * 1.0011, 2), "가격으로 ", nowPositionAmt - minAmt * 2, "만큼 팔기")
    print(round(getEntryPrice() * 1.0022, 2), "가격으로 ", minAmt * 2, "만큼 팔기")


def checkAndBuy(term):
    if term == 5:
        if checkIfGoodToBuy():
            print("사기 좋군  ", datetime.now())
            buy()
    elif term == 15:
        if checkIfGoodToWater():
            water()
