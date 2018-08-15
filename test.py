
#from exchanges.okex.OKexService import okexFuture
from exchanges.huobi.HuobiproService import huobipro


from twisted.internet import reactor

from cycle.cycle import Cycle

import urllib
import time

pairs = ('eth', 'usdt')

def test():

    #d = okexFuture.cancle(('ltc', 'usdt'), orderId=1276330619587584)
    d = huobipro.getOrder('10145765657')

    def cbPrint(result):
        print(result)
        return result

    def ebPrint(failure):
        print(failure.getBriefTraceback())
        reactor.stop()

    d.addCallback(cbPrint)
    d.addErrback(ebPrint)

    return d

#tickerCycle = Cycle(reactor, okexFuture.getTicker, 'getTicker')
#tickerCycle.start(pairs)
reactor.callWhenRunning(test)
reactor.run()
