

import json
import time

from twisted.internet import defer, task
from twisted.internet import reactor
from request import get
from utils import calcMean
from exchange import verifyExchanges
from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex

from exchange import OrderBooks

count = 0

orderBooks = OrderBooks(['gateio', 'bitfinex'], ('eth', 'usdt'))
orderBooks.start(reactor)


def cbRun():
    global count
    count += 1
    print(count)
    # time.sleep(1)
    exchangeState = dict()

    hasData = True

    for exchange, slot in orderBooks.slots.items():
        bids, asks = slot.getOrderBook()
        exchangeState[exchange] = dict()
        if len(bids) == 0:
            hasData = False
        avgBids = calcMean(bids)
        if exchange == 'gateio':
            avgAsks = calcMean(asks, True)
        else:
            avgAsks = calcMean(asks)

        exchangeState[exchange]['actual'], exchangeState[exchange]['avg'] = [bids, asks], [avgBids, avgAsks]

    # print(exchangeState)

    if hasData:
        exchangePairs = verifyExchanges(exchangeState)
        print(exchangePairs)

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
