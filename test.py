
from exchanges.okex.OKexService import okexFuture


from twisted.internet import reactor

from cycle.cycle import Cycle

import urllib
import time

pairs = ('eth', 'usdt')

def test():



    # d.addCallback(calc)
    def cbPrint(result):
        print(result)
        return result

    def ebPrint(failure):
        print(failure.getBriefTraceback())
        reactor.stop()

    d.addCallback(cbPrint)
    d.addErrback(ebPrint)

    return d

tickerCycle = Cycle(okexFuture.getTicker, 'getTicker')
tickerCycle.start(reactor, pairs)
# reactor.callWhenRunning(test)
reactor.run()
