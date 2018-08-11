from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex
from exchanges.okex.OKexService import okexFuture
from exchanges.huobi.HuobiproService import huobi

from twisted.internet import reactor
from requestUtils.request import get, post
from utils import to_bytes, calcMAs, calcBolls
from exchanges.gateio.HttpUtil import getSign
from exchanges.gateio.gateio_key import ApiKey, SecretKey
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
