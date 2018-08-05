from exchanges.gateio.GateIOService import gateio
from twisted.internet import reactor
from request import get, post
from utils import to_bytes
from exchanges.gateio.HttpUtil import getSign
from exchanges.gateio.gateio_key import ApiKey, SecretKey

import urllib

def test():

    # 在这里放你想测试的异步函数(返回一个Deferred的函数)
    # d = gateio.getOrderBook(('eth', 'usdt'))

    params = {'currencyPair': 'eth_usdt','rate':'1', 'amount':'2'}
    headers = {
        "Content-type": ["application/x-www-form-urlencoded"],
        'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'],
        'KEY': [ApiKey],
        'SIGN': [getSign(params, SecretKey)]
    }
    # params = {'symbol': 'ethusdt',
    #           'type': 'step0'}
    postdata = urllib.parse.urlencode(params)
    # d = get(
    #     reactor,
    #     url="https://api.huobi.pro/market/depth?" + postdata,
    #     headers=headers,
    # )

    d = post(
        reactor,
        url="https://api.gateio.io/api2/1/private/buy",
        headers=headers,
        body=postdata
    )


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
