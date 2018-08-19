
from exchanges.okex.OKexService import okexFuture
# from exchanges.huobi.HuobiproService import huobipro
# from exchanges.gateio.GateIOService import gateio
# from exchanges.bitfinex.BitfinexService import bitfinex
from requestUtils.request import get, post


from twisted.internet import reactor

from cycle.cycle import Cycle

import urllib
import time

pairs = ('eth', 'usdt')

start = time.time()

def test():
    url = 'http://open.yobtc.cn/app'
    resource = '/trademarket/v1/api/kline'
    headers = {
        "Content-type": ["application/x-www-form-urlencoded"],
        'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'],
    }
    params = {
        'market': 'btc_usdt',
        'type': '1min',
        'since': str(int(time.time()) - 30 * 60),
        'size': 30
    }
    postdata = urllib.parse.urlencode(params)
    # print(url + resource + '?' + postdata)
    d = get(
        reactor,
        url=url + resource + '?' + postdata,
        headers=headers
    )



    def cbPrint(result):
        now = time.time()
        print(now - start, len(result))
        return result

    def ebPrint(failure):
        print(failure.getBriefTraceback())
        reactor.stop()

    d.addCallback(cbPrint)
    d.addErrback(ebPrint)

    return d

tickerCycle = Cycle(reactor, test, 'test')
tickerCycle.start()
# reactor.callWhenRunning(test)
reactor.run()
