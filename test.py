
#from exchanges.okex.OKexService import okexFuture
from exchanges.huobi.HuobiproService import huobi


from twisted.internet import reactor

from cycle.cycle import Cycle

import urllib
import time

pairs = ('eth', 'usdt')

def test():

    d = huobi.getOrderHistory(pairs,"2018-02-13","2018-08-12")


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
