

import json
import time

from twisted.internet import defer
from twisted.internet import reactor
from request import get
from exchanges.gateio.GateIOService import gateio


def cbCondition(body1, body2):
    ob1 = json.loads(body1)
    ob2 = json.loads(body2)
    print(ob1['asks'][0], ob2['bids'][0])

@defer.inlineCallbacks
def cbNext():
    print('looping')
    time.sleep(1)
    # d = task.deferLater(reactor, 0, main, reactor)
    try:
        bids, asks = yield gateio.getOrderBook(('eth', 'usdt'))
        # body2 = yield getData(reactor, b"https://api.huobi.pro/market/depth?symbol=ethusdt&type=step0")
        # body2 = yield get(reactor, b"https://api.bitfinex.com/v1/book/ETHUSD")
        # print(body2)
    except Exception as err:
        print(err)
    print(len(bids))

    yield cbNext()


reactor.callWhenRunning(cbNext)
reactor.run()
