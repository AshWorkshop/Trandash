

import json
import time

from twisted.internet import defer, task
from twisted.internet import reactor
from requestUtils.request import get
from utils import calcMean
from exchange import verifyExchanges
from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex
from exchanges.huobi.HuobiproService import huobi

from exchange import OrderBooks

count = 0

orderBooks = OrderBooks(['gateio', 'bitfinex'], ('eth', 'usdt'))
orderBooks.start(reactor)


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

    if hasData:
        exchangePairs = verifyExchanges(exchangeState)
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
