

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

def cbCondition(body1, body2):
    ob1 = json.loads(body1)
    ob2 = json.loads(body2)
    print(ob1['asks'][0], ob2['bids'][0])

@defer.inlineCallbacks
def cbNext():
    global count
    print('Loop:', count)
    count += 1
    # time.sleep(1)
    # d = task.deferLater(reactor, 0, main, reactor)
    try:
        bids1, asks1 = yield gateio.getOrderBook(('eth', 'usdt'))
        # print(len(bids1))
        bids2, asks2 = yield bitfinex.getOrderBook(('eth', 'usdt'))
        # print(len(bids2))
    except Exception as err:
        print(err)
    # print(len(bids1), len(bids2))
    try:
        exchangeState = dict()

        exchangeState['gateio'] = dict()
        exchangeState['bitfinex'] = dict()

        avgBids1 = calcMean(bids1)
        avgAsks1 = calcMean(asks1, True)

        # print(avgBids1)

        exchangeState['gateio']['actual'], exchangeState['gateio']['avg'] = [bids1, asks1], [avgBids1, avgAsks1]

        avgBids2 = calcMean(bids2)
        avgAsks2 = calcMean(asks2)

        # print(avgBids2)

        exchangeState['bitfinex']['actual'], exchangeState['bitfinex']['avg'] = [bids2, asks2], [avgBids2, avgAsks2]
    except Exception as err:
        print(err)

    exchangePairs = verifyExchanges(exchangeState)
    print(exchangePairs)


    yield cbNext()

orderBooks = OrderBooks(['gateio', 'bitfinex'], ('eth', 'usdt'))
orderBooks.start(reactor)


def cbRun():
    global count
    count += 1
    print(count)
    time.sleep(1)
    for exchange, slot in orderBooks.slots.items():
        bids, asks = slot.getOrderBook()
        if len(bids) > 0:
            print(exchange, ': ', bids[0], asks[0])

    # yield cbRun()

# reactor.callWhenRunning(cbRun)
loop = task.LoopingCall(cbRun)

loopDeferred = loop.start(1)

reactor.run()
