

import json
import time
import shelve
from sys import argv

from twisted.internet import defer, task
from twisted.internet import reactor
from twisted.python.failure import Failure


from exchanges.okex.OKexService import okexFuture
from cycle.cycle import Cycle
from utils import calcMAs, calcBolls

if len(argv) == 4:
    _, coin, money, dataFile = argv
else:
    print("ERROR!")
    quit()

count = 0
total = 0
wait = 0
leverage = 20
buys = []
sells = []
buypId = None
sellpId = None
maxRight = 0.0
maxRightEveryPeriod = 0.0
maxDrawdown = 0.0
klineCycle = Cycle(reactor, okexFuture.getKLineLastMin, 'getKLineLastMin')
tickerCycle = Cycle(reactor, okexFuture.getTicker, 'getTicker')
positionCycle = Cycle(reactor, okexFuture.getPosition, 'getPosition', limit=5)
userInfoCycle = Cycle(reactor, okexFuture.getUserInfo, 'getUserInfo', limit=5)
orderBookCycle = Cycle(reactor, okexFuture.getOrderBook, 'getOrderBook')

pairs = (coin, money)
klineCycle.start(pairs, last=100)
tickerCycle.start(pairs)
positionCycle.start(pairs)
orderBookCycle.start(pairs)
userInfoCycle.start(coin)

state = 'FIRST'

@defer.inlineCallbacks
def buy(amount=1.0, price=""):
    global state
    global buys
    orderId = None
    try:
        if price:
            matchPrice = "0"
        else:
            matchPrice = "1"
        orderId = yield okexFuture.trade(pairs, price=price, amount=str(round(amount)), tradeType="1", matchPrice=matchPrice)
        print(orderId)
    except Exception as err:
        failure = Failure(err)
        print(failure.getBriefTraceback())

    if orderId:
        print("SUCCESSFULLY BUY:", orderId)
        try:
            order = yield okexFuture.getOrder(pairs, orderId=orderId)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())
        else:
            print(order)
            price = order[0]['price']
            buys.append((price, float(amount)))
            data = shelve.open(dataFile)
            data['buys'] = buys
            data.close()
            # time.sleep(1)


    state = 'GO'

@defer.inlineCallbacks
def buyp(amount, price="", sellAmount=0):
    global state
    global buys
    global buypId
    orderId = None
    try:
        if price == "":
            matchPrice = "1"
        else:
            matchPrice = "0"
        orderId = yield okexFuture.trade(pairs, price=price, amount=str(round(amount)), tradeType="3", matchPrice=matchPrice)
    except Exception as err:
        failure = Failure(err)
        print(failure.getBriefTraceback())

    if orderId:
        print("SUCCESSFULLY BUYP:", orderId)

        try:
            order = yield okexFuture.getOrder(pairs, orderId=orderId)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())
        else:
            print(order)

    buypId = orderId
    if state == 'PPP':
        state = 'PPPsell'
        if sellAmount > 0:
            reactor.callWhenRunning(sellp, amount=sellAmount)
    else:
        state = 'BUYPCHECK'


@defer.inlineCallbacks
def sell(amount=1.0, price=""):
    global state
    global sells
    orderId = None
    try:
        if price:
            matchPrice = "0"
        else:
            matchPrice = "1"
        orderId = yield okexFuture.trade(pairs, price=price, amount=str(round(amount)), tradeType="2", matchPrice=matchPrice)
        print(orderId)
    except Exception as err:
        failure = Failure(err)
        print(failure.getBriefTraceback())

    if orderId:
        print("SUCCESSFULLY SELL:", orderId)
        try:
            order = yield okexFuture.getOrder(pairs, orderId=orderId)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())
        else:
            print(order)
            price = order[0]['price']
            sells.append((price, float(amount)))
            data = shelve.open(dataFile)
            data['sells'] = sells
            data.close()
            # time.sleep(1)
    state = 'GO'

@defer.inlineCallbacks
def sellp(amount, price=""):
    global state
    global sells
    global sellpId
    orderId = None
    try:
        if price == "":
            matchPrice = "1"
        else:
            matchPrice = "0"
        orderId = yield okexFuture.trade(pairs, price=price, amount=str(round(amount)), tradeType="4", matchPrice=matchPrice)
        print(orderId)
    except Exception as err:
        failure = Failure(err)
        print(failure.getBriefTraceback())

    if orderId:
        print("SUCCESSFULLY SELLP:", orderId)
        try:
            order = yield okexFuture.getOrder(pairs, orderId=orderId)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())
        else:
            print(order)


    sellpId = orderId

    if state == 'PPPsell':
        state = 'STOP'
    else:
        state = 'SELLPCHECK'

@defer.inlineCallbacks
def cancle(orderId):
    global state
    result = False
    data = -1
    try:
        result, data = yield okexFuture.cancle(pairs, orderId=orderId)
    except Exception as err:
        failure = Failure(err)
        print(failure.getBriefTraceback())

    if result:
        print('SUCCESSFULLY CANCLE:', orderId)
        state = 'GO'
    elif data == 20015:
        print('SUCCESSFULLY CANCLE:', orderId)
        state = 'GO'

# def get_buy_avg_price(buys):
#     for buy in buys:

def getAvg(things):
    total = 0
    totalAmount = 0
    for price, amount in things:
        amount = round(amount)
        total += price * amount
        totalAmount += amount
    if totalAmount == 0:
        return 0
    return total / totalAmount

def cbRun():
    global count
    global state
    global wait
    global total
    global buys
    global sells
    global buypId
    global sellpId
    global maxRight
    global maxRightEveryPeriod
    global maxDrawdown
    count += 1
    wait += 1
    print('[', count, state, ']')
    # time.sleep(1)
    if state == 'FIRST':
        data = shelve.open(dataFile)
        buys = data.get('buys', [])
        sells = data.get('sells', [])
        print('buys && sells:', buys, sells)
        state = 'GO'

    KLinesData = klineCycle.getData()
    tickerData = tickerCycle.getData()
    positionData = positionCycle.getData()
    orderBookData = orderBookCycle.getData()
    userInfoData = userInfoCycle.getData()

    print(bool(KLinesData), bool(tickerData), bool(positionData), bool(orderBookData), bool(userInfoData))

    if state == 'GO':
        # print(len(klines), ticker, position)
        # 是否开初始单
        if KLinesData is not None and tickerData is not None and positionData is not None:
            total += 1
            wait -= 1
            print('avg wait:', wait / total)

            MAs = calcMAs(KLinesData, ma=30)
            position = positionData
            buy_amount = position['buy_amount']
            sell_amount = position['sell_amount']
            timestamp, ma = MAs[-1]

            ticker = tickerData['last']

            print('ticker && ma:', ticker, ma)
            print('buy_amount && sell_amount:', buy_amount, sell_amount)

            if ticker > ma and buy_amount == 0 and len(buys) == 0:
                print('BUY')
                state = 'WAIT'
                reactor.callWhenRunning(buy)
                # reactor.callWhenRunning(buy)

            if ticker < ma and sell_amount == 0 and len(sells) == 0:
                print('SELL')
                state = 'WAIT'
                reactor.callWhenRunning(sell)

        # 是否平
        if orderBookData != None and positionData != None:
            position = positionData
            # print(position)
            bids, asks = orderBookData
            buy2, _ = bids[1]
            sell2, _ = asks[1]
            buy_price_avg = getAvg(buys)
            sell_price_avg = getAvg(sells)
            buy_amount = position['buy_amount']
            sell_amount = position['sell_amount']
            # print(position)
            buy_profit = position['buy_profit_real']
            sell_profit = position['sell_profit_real']

            print('buy_price_avg && buy2:', buy_price_avg, buy2)
            print('sell_price_avg && sell2:', sell_price_avg, sell2)

            if buy_price_avg == 0:
                buyRate = 0
            else:
                buyRate = (buy2 - buy_price_avg) / buy_price_avg * leverage

            if sell_price_avg == 0:
                sellRate = 0
            else:
                sellRate = (sell_price_avg - sell2) / sell_price_avg * leverage

            print('buyRate && sellRate:', buyRate, sellRate)

            if buyRate >= 0.03 and buy_amount != 0:
                print('BUYP')
                state = 'WAIT'
                reactor.callWhenRunning(buyp, amount=buy_amount, price=str(buy2))


            if sellRate >= 0.03 and sell_amount != 0:
                print('SELLP')
                state = 'WAIT'
                reactor.callWhenRunning(sellp, amount=sell_amount, price=str(sell2))



        # 布林
        if tickerData != None and KLinesData != None and positionData != None:
            ticker = tickerData['last']
            KLines = KLinesData
            position = positionData
            buy_amount = position['buy_amount']
            sell_amount = position['sell_amount']

            Bolls = calcBolls(KLines)
            klines = KLines[-3:]
            bolls = Bolls[-3:]
            llk, lk, k = klines
            llb, lb, b = bolls
            _, _, _, _, llk_close, _, _ = llk
            _, _, _, _, lk_close, _, _ = lk
            _, llb_u, _, llb_d = llb
            _, lb_u, _, lb_d = lb
            _, b_u, _, b_d = b
            if llk_close > llb_d and lk_close < lb_d:
                print('BUYBOLL')
                if buy_amount > 0:
                    buy_price_last, buy_amount_last = buys[-1]
                    if (buy_price_last - ticker) / buy_price_last >= 0.005:
                        if len(buys) < 6:
                            buy_amount_new = buy_amount_last * 1.618
                        else:
                            buy_amount_new = buy_amount_last
                        print('BUY', buy_amount_new)
                        state = 'WAIT'
                        reactor.callWhenRunning(buy, amount=buy_amount_new)

            if llk_close < llb_u and lk_close > lb_u:
                print('SELLBOLL')
                if sell_amount > 0:
                    sell_price_last, sell_amount_last = sells[-1]
                    if (ticker - sell_price_last) / sell_price_last >= 0.005:
                        if len(sells) < 6:
                            sell_amount_new = sell_amount_last * 1.618
                        else:
                            sell_amount_new = sell_amount_last
                        print('SELL', sell_amount_new)
                        state = 'WAIT'
                        reactor.callWhenRunning(sell, amount=sell_amount_new)
        if userInfoData is not None and positionData is not None:
            # 止损
            account_rights = userInfoData['account_rights']
            keep_deposit = userInfoData['keep_deposit']
            profit_real = userInfoData['profit_real']
            profit_unreal = userInfoData['profit_unreal']

            position = positionData
            buy_amount = position['buy_amount']
            sell_amount = position['sell_amount']

            print('account_rights && keep_deposit:', account_rights, keep_deposit)
            print('profit_real && profit_unreal:', profit_real, profit_unreal)

            if account_rights > maxRight:
                maxRight = account_rights
            print('maxRight:', maxRight)

            if -(profit_real + profit_unreal) > 0.5 * maxRight and buy_amount > 0:
                print('PPP')
                state = 'PPP'
                reactor.callWhenRunning(buyp, amount=buy_amount, sellAmount=sell_amount)

        if userInfoData is not None:
            account_rights = userInfoData['account_rights']
            if maxRightEveryPeriod < account_rights:
                maxRightEveryPeriod = account_rights
            if maxRightEveryPeriod != 0.0:
                drawdown = (maxRightEveryPeriod - account_rights) / maxRightEveryPeriod
            else:
                drawdown = 0.0

            if drawdown > maxDrawdown:
                maxDrawdown = drawdown


        if count % 60 == 0:
            maxRightEveryPeriod = 0.0
            staFile = open('okex_' + coin, 'a+')
            staFile.write("%d,%d" % (count, maxDrawdown))
            staFile.close()





            # if 0.7 * (1.0 + maxProfit) <= - (buyRate + sellRate) and buy_amount != 0:


    if state == 'STOP':
        print('************** STOP **************')
        reactor.stop()

    if state == 'BUYPCHECK':
        if positionData is not None:
            buy_amount = positionData['buy_amount']
            if buy_amount == 0:
                buys = []
                data = shelve.open(dataFile)
                data['buys'] = buys
                data.close()
                buypId = None
                state = 'GO'
            else:
                reactor.callWhenRunning(cancle, buypId)


    if state == 'SELLPCHECK':
        if positionData is not None:
            sell_amount = positionData['sell_amount']
            if sell_amount == 0:
                sells = []
                data = shelve.open(dataFile)
                data['sells'] = sells
                data.close()
                sellpId = None
                state = 'GO'
            else:
                reactor.callWhenRunning(cancle, sellpId)










    # yield cbRun()
def ebLoopFailed(failure):
    """
    Called when loop execution failed.
    """
    print(failure.getBriefTraceback())
    # reactor.stop()


# d = defer.Deferred()
# d = task.deferLater(reactor, 1, cbRun, d)
# d.addErrback(ebLoopFailed)
loop = task.LoopingCall(cbRun)

loopDeferred = loop.start(1.0)
loopDeferred.addErrback(ebLoopFailed)

reactor.run()
