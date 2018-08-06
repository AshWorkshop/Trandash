

import json
import time

from twisted.internet import defer, task
from twisted.internet import reactor


from exchanges.okex.OKexService import okexFuture


count = 0

@defer.inlineCallbacks
def priceCycle():
    pairs = ('eth', 'usdt')
    bids, asks = yield okexFuture.getOrderBook(pairs)
    print(bids, asks)

    yield priceCycle()

def cbRun():
    global count
    count += 1
    # print(count)
    # time.sleep(1)
    pairs = ('eth', 'usdt')
    d = okexFuture.getOrderBook(pairs)
    def cbPrint(result):
        print(result)
        return result

    def ebPrint(failure):
        print(failure.getBriefTraceback())
        reactor.stop()

    d.addCallback(cbPrint)
    d.addErrback(ebPrint)

    # yield cbRun()
def ebLoopFailed(failure):
    """
    Called when loop execution failed.
    """
    print(failure.getBriefTraceback())
    reactor.stop()

reactor.callWhenRunning(myTask)
# loop = task.LoopingCall(cbRun)

# loopDeferred = loop.start(1.0)
# loopDeferred.addErrback(ebLoopFailed)

reactor.run()
