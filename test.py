from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex
# from exchanges.okex.OKexService import okexFuture
# from exchanges.huobi.HuobiproService import huobi

from twisted.internet import reactor
from requestUtils.request import get, post
from utils import to_bytes, calcMAs, calcBolls
from exchanges.gateio.HttpUtil import getSign
from exchanges.gateio.gateio_key import ApiKey, SecretKey

import urllib
import time

def test():


    # test of bitfinex:
    pairs = ('eth', 'usdt')
    # d = bitfinex.cancel(pairs,15172894785)
    # d = bitfinex.getOrder(pairs,15172894785)
    # d = bitfinex.sell(pairs,409,0.02)  #ps. fail to test buy() because money is not enough LOL
    # d = bitfinex.getOrderBook(pairs)
    # d = bitfinex.getBalance('eth')
    d = bitfinex.getOrderHistory(pairs, givenTime=1531065600)   #1531065600:2018/7/9 0:0:0
    

    def calc(KLines):
        # print(KLines[-3:])
        return (calcMAs(KLines), KLines[-2:], calcBolls(KLines)[-2:])

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

reactor.callWhenRunning(test)
reactor.run()
