
#from exchanges.okex.OKexService import okexFuture
# from exchanges.huobi.HuobiproService import huobipro
from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex


from twisted.internet import reactor

from cycle.cycle import Cycle

import urllib
import time

pairs = ('eth', 'usdt')

def test():

    #d = okexFuture.cancle(('ltc', 'usdt'), orderId=1276330619587584)
    # d = huobipro.buy(('eth','usdt'),290,500)
    #d = huobipro.getBalances(['eth','usdt'])
    #d = bitfinex.getOrderBook(pairs)
    d = bitfinex.getBalances(['eth','usdt','eos'])
    # d = bitfinex.sell(('eth','usdt'),284.24,0.1)
    # d = bitfinex.getOrder(pairs,15622582761)
    # d = bitfinex.getOrderHistory(pairs,1534608693)


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
