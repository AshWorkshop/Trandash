
#from exchanges.okex.OKexService import okexFuture
from exchanges.huobi.HuobiproService import huobipro
from exchanges.gateio.GateIOService import gateio
# from exchanges.bitfinex.BitfinexService import bitfinex


from twisted.internet import reactor

from cycle.cycle import Cycle

import urllib
import time

pairs = ('eth', 'usdt')

def test():

    d = huobipro.getOrderHistory(pairs = pairs,start_date = "2018-8-1",end_date = "2018-8-19")
    #d = okexFuture.cancle(('ltc', 'usdt'), orderId=1276330619587584)
    #d = huobipro.sell(coinPair=('eth','usdt'),price=293,amount=0.05)
    #d = huobipro.getBalances(['eth','usdt'])
    #d = gateio.getBalances(['eth','usdt'])
    #d = gateio.getOrder(1209262944,pairs)
    #d = gateio.buy(coinPair=('eth','usdt'),price=292.9,amount=0.05)
    # d = bitfinex.getOrderBook(('eos', 'eth'))


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
