

import json
import time

from twisted.internet import defer, task
from twisted.internet import reactor
from requestUtils.request import get
from utils import calcMean
from exchange import verifyExchanges
from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex
from exchanges.huobi.HuobiproService import huobipro

from exchange import OrderBooks

count = 0

orderBooks = OrderBooks(['gateio', 'huobipro'], ('eth', 'usdt'))
SELL,BUY = range(2)
EXCHANGE = {
    'huobipro': huobipro,
    'gateio': gateio,
    'bitfinex': bitfinex
}
orderBooks.start(reactor)
state = 'FIRST'


@defer.inlineCallbacks
def buy(exchange,coinPair,amount,price):
    print(exchange,amount,price)
    print(exchange.getBalance(coinPair(BUY)))
    orderId = None
    if exchange.getBalance(coinPair[BUY]) >= price*amount:
        try:
            orderId = yield exchange.buy(coinPair,price,amount)
            print(orderId)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())

    if orderId[0] == True:
        print("SUCCESSFULLY BUY:", orderId[1])
        try:
            order = yield exchange.getOrder(orderId,coinPair)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())

    state = "GO"

@defer.inlineCallbacks
def sell(exchange,coinPair,amount,price):
    global state
    orderId = None
    if exchange.getBalance(coinPair[SELL]) >= amount:
        try:
            orderId = yield exchange.sell(coinPair,price,amount)
            print(orderId)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())

    if orderId[0] == True:
        print("SUCCESSFULLY SELL:", orderId[1])
        try:
            order = yield exchange.getOrder(orderId,coinPair)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())

    state = "GO"

def cbRun():
    global count
    global state
    count += 1
    # print(count)
    # time.sleep(1)
    exchangeState = dict()

    hasData = True

    for exchange, slot in orderBooks.slots.items():
        bids, asks = slot.getOrderBook()
        slot.setOrderBook()
        exchangeState[exchange] = dict()
        if len(bids) == 0:
            hasData = False
            break
        avgBids = calcMean(bids) #买单
        avgAsks = calcMean(asks) #卖单

        exchangeState[exchange]['actual'], exchangeState[exchange]['avg'] = [bids, asks], [avgBids, avgAsks]

    #print(exchangeState)

    if hasData:
        exchangePairs = verifyExchanges(exchangeState)
        print(count, exchangePairs)
        if exchangePairs:
            print('BUY')
            exchange = EXCHANGE[exchangePairs[0][0][BUY]]
            price  = exchangePairs[0][1][BUY]
            amount = exchangePairs[0][2][1]
            #print(exchange.getBalance('usdt'),price,amount)
            reactor.callWhenRunning(buy,exchange=exchange,coinPair=orderBooks.pairs,price=price,amount=amount)

            print('SELL')
            exchange = EXCHANGE[exchangePairs[0][0][SELL]]
            price  = exchangePairs[0][1][SELL]
            amount = exchangePairs[0][2][1]
            reactor.callWhenRunning(buy,exchange=exchange,coinPair=orderBooks.pairs,price=price,amount=amount)

def ebLoopFailed(failure):
    """
    Called when loop execution failed.
    """
    print(failure.getBriefTraceback())
    reactor.stop()

# reactor.callWhenRunning(cbRun)
loop = task.LoopingCall(cbRun)

loopDeferred = loop.start(1.0)
loopDeferred.addErrback(ebLoopFailed)

reactor.run()
