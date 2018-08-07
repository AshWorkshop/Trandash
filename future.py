

import json
import time

from twisted.internet import defer, task
from twisted.internet import reactor
from twisted.python.failure import Failure


from exchanges.okex.OKexService import okexFuture
from cycle.OKExCycle import KLineCycle, TickerCycle, PositionCycle, OrderBookCycle
from utils import calcMAs, calcBolls


count = 0
total = 0
wait = 0
buys = []
klineCycle = KLineCycle('okexFuture')
tickerCycle = TickerCycle('okexFuture')
positionCycle = PositionCycle('okexFuture')
orderBookCycle = OrderBookCycle('okexFuture')

pairs = ('eth', 'usdt')
klineCycle.start(reactor, pairs, last=200)
tickerCycle.start(reactor, pairs)
positionCycle.start(reactor, pairs)
orderBookCycle.start(reactor, pairs)

state = 'GO'

@defer.inlineCallbacks
def buy(amount="1", price=""):
    global state
    orderId = None
    try:
        if price:
            matchPrice = "0"
        else:
            matchPrice = "1"
        orderId = yield okexFuture.trade(pairs, price=price, amount=amount, tradeType="1", matchPrice=matchPrice)
        print(orderId)
    except Exception as err:
        failure = Failure(err)
        print(failure.getBriefTraceback())

    if orderId:
        print("SUCCESSFULLY BUY:", orderId)
    state = 'GO'
    
def cbRun():
    global count
    global state
    global wait
    global total
    count += 1
    wait += 1
    print('[', count, state, ']')
    # time.sleep(1)
    if state != 'WAIT':
        KLinesData = klineCycle.getData()
        tickerData = tickerCycle.getData()
        positionData = positionCycle.getData()
        orderBookData = orderBookCycle.getData()
        # print(len(klines), ticker, position)
        if KLinesData != {} and tickerData != {} and positionData != {}:
            total += 1
            wait -= 1
            print('avg wait:', wait / total)
            MAs = calcMAs(KLinesData['klines'])
            position = positionData['position']
            buy_amount = position['buy_amount']
            sell_amount = position['sell_amount']
            timestamp, ma = MAs[-1]

            ticker = tickerData['ticker']['last']

            # print(ticker, ma)
            print(buy_amount, sell_amount)

            if ticker > ma and buy_amount == 0:
                print('BUY')
                state = 'GO'
                # reactor.callWhenRunning(buy)

        if orderBookData != {} and positionData != {}:
            position = positionData['position']
            bids, asks = orderBookData['orderBook']
            buy2, _ = bids[1]
            sell2, _ = asks[1]
            buy_price_avg = position['buy_price_avg']
            sell_price_avg = position['sell_price_avg']
            buy_amount = position['buy_amount']
            sell_amount = position['sell_amount']

            print(buy_price_avg, sell2)

            rate = (sell2 - buy_price_avg) / buy_price_avg
            
            print(rate)

            if rate >= 0.01 and buy_amount != 0:
                print('BUYP')

        if tickerData != {} and KLinesData != {} and positionData != {}:
            ticker = tickerData['ticker']['last']
            KLines = KLinesData['klines']
            Bolls = calcBolls(KLines)
            klines = KLines[-3:]
            bolls = Bolls[-3:]
            llk, lk, k = klines
            llb, lb, b = bolls
            _, _, _, _, llk_close, _, _ = llk
            _, _, _, _, lk_close, _, _ = lk
            _, _, _, llb_d = llb
            _, _, _, lb_d = lb
            if llk_close > llb_d and lk_close < lb_d and ticker < b:
                print('BOLL')
                if len(buys) > 0:
                    last = buys[-1]
                    last_price = last['price']
                    if (last_price - ticker) / last_price >= 0.001:
                        print('BUY', len(buys))




            


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
