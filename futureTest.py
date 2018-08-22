
from exchanges.okex.OKexService import okexFuture
# from exchanges.huobi.HuobiproService import huobipro
# from exchanges.gateio.GateIOService import gateio
# from exchanges.bitfinex.BitfinexService import bitfinex
from exchanges.sisty.sisty_key import MD5Key
from exchanges.sisty.SistyService import sisty
from requestUtils.request import get, post


from twisted.internet import reactor, task

from cycle.cycle import Cycle

import urllib
import hashlib
import time
import json

pairs = ('eth', 'usdt')

start = time.time()

def test():
    d = sisty.trade(pairs, 265.46, 1, 0)
    def cbTest(result):
        print(result)
        return result

    def ebTest(failure):
        print(failure)
    d.addCallback(cbTest)
    d.addErrback(ebTest)

def fun():
    print('Testing!')
    json.loads('T')
    return "Testing!"

def cbPrint(result):
    data = json.loads(result)
    return data

def ebPrint(failure):
    print(failure)
    return None

def cycleTest():
    d = task.deferLater(reactor, 1, fun)
    d.addCallback(cbPrint)
    d.addErrback(ebPrint)

    return d

    


cycle = Cycle(reactor, cycleTest, 'test')
cycle.start()
# reactor.callWhenRunning(test)
print(cycle.getData())
reactor.run()
