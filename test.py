from exchanges.gateio.GateIOService import gateio
from exchanges.huobi.HuobiproService import huobi
from exchanges.bitfinex.BitfinexService import bitfinex
from twisted.internet import reactor

def test():

    # 在这里放你想测试的异步函数(返回一个Deferred的函数)
    d = huobi.getOrderBook(('eth', 'usdt'))

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
