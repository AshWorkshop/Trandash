
#from exchanges.okex.OKexService import okexFuture
# from exchanges.huobi.HuobiproService import huobipro
from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex
from exchanges.sisty.SistyService import sisty


from twisted.internet import reactor

from cycle.cycle import Cycle

import urllib
import time

pairs = ('eth', 'usdt')

def test():

    #d = huobipro.getOrderHistory(pairs = pairs,start_date = "2018-8-1",end_date = "2018-8-19")
    #d = okexFuture.cancle(('ltc', 'usdt'), orderId=1276330619587584)
    #d = huobipro.sell(coinPair=('eth','usdt'),price=293,amount=0.05)
    #d = huobipro.getBalances(['eth','usdt'])
    #d = gateio.getBalances(['eth','usdt'])
    #d = gateio.getOrder(1209262944,pairs)
    #d = gateio.buy(coinPair=('eth','usdt'),price=292.9,amount=0.05)
    # d = huobipro.buy(('eth','usdt'),290,500)
    # d = huobipro.getBalances(['eth','usdt'])

    # d = bitfinex.getOrderBook(pairs)
    # d = bitfinex.getBalances(['eth','usdt','eos'])
    # d = bitfinex.sell(('eth','usdt'),291.09,0.2)
    # d = bitfinex.getOrder(pairs,15638551536)
    # d = bitfinex.getOrderHistory(pairs,1534608693)
    d = sisty.getOrders(pairs)


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
