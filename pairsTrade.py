

import json
import time

from twisted.internet import defer, task
from twisted.internet import reactor
from requestUtils.request import get
from utils import calcMean
from exchange import calcVirtualOrderBooks, verifyExchanges
from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex
from exchanges.huobi.HuobiproService import huobipro

from exchange import OrderBooks

count = 0

orderBooks = OrderBooks( ['bitfinex'], ('eos', 'usdt'))
orderBooks.start(reactor)
orderBookA = OrderBooks( ['bitfinex'], ('eth', 'usdt'))
orderBookA.start(reactor)
orderBookB = OrderBooks( ['bitfinex'], ('eos', 'eth'))
orderBookB.start(reactor)

def cbRun():
    global count
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
        avgBids = calcMean(bids)
        avgAsks = calcMean(asks)

        exchangeState[exchange]['actual'], exchangeState[exchange]['avg'] = [bids, asks], [avgBids, avgAsks]
    
    # print(exchangeState)

    A = []
    B = []
    for exchange, slot in orderBookA.slots.items():
        bids, asks = slot.getOrderBook()
        slot.setOrderBook()
        # print(bids)
        # print(asks)
        
        if len(bids) == 0:
            hasData = False
            break
        A= [bids, asks]

    for exchange, slot in orderBookB.slots.items():
        bids, asks = slot.getOrderBook()
        slot.setOrderBook()
        exchangeState[exchange] = dict()
        if len(bids) == 0:
            hasData = False
            break   
        B= [bids, asks] 

    if hasData:
        exchangePairs = verifyExchanges(exchangeState)
        # print(count, exchangePairs)
        VirtualOrderBooks = calcVirtualOrderBooks(A, B)
        print(count, VirtualOrderBooks)


    # yield cbRun()
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