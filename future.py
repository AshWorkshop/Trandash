

import json
import time
import shelve

from twisted.internet import defer, task
from twisted.internet import reactor
from twisted.python.failure import Failure


from exchanges.okex.OKexService import okexFuture
from cycle.OKExCycle import KLineCycle, TickerCycle, PositionCycle, OrderBookCycle
from cycle.cycle import Cycle
from utils import calcMAs, calcBolls


count = 0
total = 0
wait = 0
leverage = 20
buys = []
sells = []
maxProfit = 0.0
klineCycle = Cycle(okexFuture.getKLineLastMin, 'getKLineLastMin')
tickerCycle = Cycle(okexFuture.getTicker, 'getTicker')
positionCycle = Cycle(okexFuture.getPosition, 'getPosition', limit=5)
orderBookCycle = Cycle(okexFuture.getOrderBook, 'getOrderBook')

pairs = ('eth', 'usdt')
klineCycle.start(reactor, pairs, last=30)
tickerCycle.start(reactor, pairs)
positionCycle.start(reactor, pairs)
orderBookCycle.start(reactor, pairs)

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
            data = shelve.open('data')
            data['buys'] = buys
            data.close()
            # time.sleep(1)
            

    state = 'GO'

@defer.inlineCallbacks
def buyp(amount, price="", sellAmount=0):
    global state
    global buys
    orderId = None
    try:
        if price == "":
            matchPrice = "1"
        else:
            matchPrice = "0"
        orderId = yield okexFuture.trade(pairs, price=price, amount=str(round(amount)), tradeType="3", matchPrice=matchPrice)
        print(orderId)
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
            buys = []
            data = shelve.open('data')
            data['buys'] = buys
            data.close()
    if state == 'PPP':
        state = 'PPPsell'
        if sellAmount > 0:
            reactor.callWhenRunning(sell, amount=sellAmount)
    else:
        state = 'GO'


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
            data = shelve.open('data')
            data['sells'] = sells
            data.close()
            # time.sleep(1)
    state = 'GO'

@defer.inlineCallbacks
def sellp(amount, price=""):
    global state
    global sells
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
            print()
            sells = []
            data = shelve.open('data')
            data['sells'] = sells
            data.close()

    if state == 'PPPsell':
        state = 'STOP'
    else:
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
    global maxProfit
    count += 1
    wait += 1
    print('[', count, state, ']')
    # time.sleep(1)
    if state == 'FIRST':
        data = shelve.open('data')
        buys = data.get('buys', [])
        sells = data.get('sells', [])
        print('buys && sells:', buys, sells)
        state = 'GO'

    KLinesData = klineCycle.getData()
    tickerData = tickerCycle.getData()
    positionData = positionCycle.getData()
    orderBookData = orderBookCycle.getData()

    if state == 'GO':
        # print(len(klines), ticker, position)
        # 是否开初始单
        if KLinesData != [] and tickerData != [] and positionData != []:
            total += 1
            wait -= 1
            print('avg wait:', wait / total)
            MAs = calcMAs(KLinesData[0], ma=30)
            position = positionData[0]
            buy_amount = position['buy_amount']
            sell_amount = position['sell_amount']
            timestamp, ma = MAs[-1]

            ticker = tickerData[0]['last']

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
        if orderBookData != [] and positionData != []:
            position = positionData[0]
            # print(position)
            bids, asks = orderBookData[0]
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

            # 止损
            if maxProfit < buy_profit + sell_profit:
                maxProfit = buy_profit + sell_profit

            print('maxProfit:', maxProfit)
            
            if 0.5 * (1.0 + maxProfit) <= - (buyRate + sellRate) and buy_amount != 0 and sell_amount != 0:
                print('PPP')
                state = 'PPP'
                reactor.callWhenRunning(buyp, amount=buy_amount, sellAmount=sell_amount)
                

        # 布林
        if tickerData != [] and KLinesData != [] and positionData != []:
            ticker = tickerData[0]['last']
            KLines = KLinesData[0]
            position = positionData[0]
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
        
    if state == 'STOP':
        print('************** STOP **************')
        reactor.stop()






            


    # yield cbRun()
def ebLoopFailed(failure):
    """
    Called when loop execution failed.
    """
    print(failure.getBriefTraceback())
    reactor.stop()


# d = defer.Deferred()
# d = task.deferLater(reactor, 1, cbRun, d)
# d.addErrback(ebLoopFailed)
loop = task.LoopingCall(cbRun)

loopDeferred = loop.start(1.0)
loopDeferred.addErrback(ebLoopFailed)

reactor.run()
