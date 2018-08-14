

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

FEE = {
    'huobipro': [1.004,0.996],
    'gateio': [1.004,0.996],
    'bitfinex': [1.004,0.996],
    'virtual': [1.004,0.996],
}

def cbRun():
    global count
    count += 1
    # print(count)
    # time.sleep(1)
    exchangeState = dict()

    hasData = True
    


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
        A = [bids, asks]

    for exchange, slot in orderBookB.slots.items():
        bids, asks = slot.getOrderBook()
        slot.setOrderBook()
        if len(bids) == 0:
            hasData = False
            break   
        B = [bids, asks] 

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

    if hasData:
        VirtualOrderBooks = calcVirtualOrderBooks(A, B)
        # print(count, VirtualOrderBooks)
        BUY, SELL = range(2)
        virBids = VirtualOrderBooks[BUY]
        virAsks = VirtualOrderBooks[SELL]
        avgVirBids = calcMean(virBids)
        avgVirAsks = calcMean(virAsks)
        exchangeState['virtual'] = dict()
        exchangeState['virtual']['actual'], exchangeState['virtual']['avg'] = [virBids, virAsks], [avgVirBids, avgVirAsks]
        exchangePairs = verifyExchanges(exchangeState,FEE=FEE)
        print(count, exchangePairs)


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