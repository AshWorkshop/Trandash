
from exchanges.okex.OKexService import okexFuture
# from exchanges.huobi.HuobiproService import huobipro
# from exchanges.gateio.GateIOService import gateio
# from exchanges.bitfinex.BitfinexService import bitfinex
from exchanges.sisty.sisty_key import MD5Key
from requestUtils.request import get, post


from twisted.internet import reactor

from cycle.cycle import Cycle

import urllib
import hashlib
import time

pairs = ('eth', 'usdt')

start = time.time()

def test():
    url = 'http://47.75.31.125/app/'
    resource = '/tradeOpen/v2/apiAddEntrustV2Robot'
    headers = {
        "Content-type": ["application/x-www-form-urlencoded"],
        'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'],
    }
    userId = str(222)
    coinName = 'eth'
    payCoinIdName = 'usdt'

    data = userId + coinName + payCoinIdName + MD5Key

    cipherText = hashlib.md5(data.encode("utf8")).hexdigest().upper()
    params = {
        'coinName': coinName,
        'payCoinName': payCoinIdName,
        'amount': 1,
        'price': 265.46,
        'type': '1',
        'cipherText': cipherText,
        'secret': '12345678',
        'userId': userId
    }
    postdata = urllib.parse.urlencode(params)
    

    # print(url + resource + '?' + postdata)
    d = post(
        reactor,
        url=url + resource,
        headers=headers,
        body=postdata
    )



    def cbPrint(result):
        now = time.time()
        print(now - start, result)
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
