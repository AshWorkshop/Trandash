
from exchanges.okex.OKexService import okexFuture
from requestUtils.request import get, post


from twisted.internet import reactor, task

from cycle.cycle import Cycle

import urllib
import hashlib
import time
import json

pairs = ('ETH', 'USDT')

start = time.time()

def test():
    d = okexFuture.getPosition(pairs)
    def cbTest(result):
        print(result)
        return result

    def ebTest(failure):
        print(failure)
    d.addCallback(cbTest)
    d.addErrback(ebTest)

def fun():
    print('Testing!')
    data = json.loads('T')
    return None

def cbPrint(result):
    print(result)
    return result

def cbPrint2(result):
    print(result)
    return result

def ebPrint(failure):
    print(failure)
    return None

def cycleTest():
    d = task.deferLater(reactor, 1, fun)
    d.addCallback(cbPrint)
    # d.addErrback(ebPrint)

    return d

def cycleTest2():
    d = cycleTest()
    d.addCallback(cbPrint2)
    d.addErrback(ebPrint)

    return d


# cycle = Cycle(reactor, cycleTest2, 'test')
# cycle.start()
reactor.callWhenRunning(test)
# print(cycle.getData())
reactor.run()
