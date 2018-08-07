

import json
import time

from twisted.internet import defer, task
from twisted.internet import reactor


from exchanges.okex.OKexService import okexFuture
from cycle.klineCycle import KLineCycle, TickerCycle
from utils import calcMAs, calcBolls


count = 0
klineCycle = KLineCycle('okexFuture')
tickerCycle = TickerCycle('okexFuture')
pairs = ('eth', 'usdt')
klineCycle.start(reactor, pairs, last=200)
tickerCycle.start(reactor, pairs)

def cbRun():
    global count
    count += 1
    print('[', count, ']')
    # time.sleep(1)
    data = klineCycle.getData()
    ticker = tickerCycle.getData()
    if data != {} and ticker != {}:
        MAs = calcMAs(data['klines'])
        Bolls = calcBolls(data['klines'])
        print(ticker['ticker']['last'])
        print(len(MAs))
        print(len(Bolls))


    # yield cbRun()
def ebLoopFailed(failure):
    """
    Called when loop execution failed.
    """
    print(failure.getBriefTraceback())
    reactor.stop()

# reactor.callWhenRunning(priceCycle)
loop = task.LoopingCall(cbRun)

loopDeferred = loop.start(1.0)
loopDeferred.addErrback(ebLoopFailed)

reactor.run()
