from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex
#from exchanges.okex.OKexService import okexFuture
from exchanges.huobi.HuobiproService import huobi

from twisted.internet import reactor
from requestUtils.request import get, post
from utils import to_bytes, calcMAs, calcBolls
from exchanges.gateio.HttpUtil import getSign
from exchanges.gateio.gateio_key import ApiKey, SecretKey

import urllib
import time

def test():

    # 在这里放你想测试的异步函数(返回一个Deferred的函数)
    d = huobi.cancelOrder(9668933237)

    # params = {'symbol': 'eth_usd', 'contract_type': 'this_week'}
    # headers = {
    #     "Content-type": ["application/x-www-form-urlencoded"],
    #     'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'],
    #     'KEY': [ApiKey],
    #     'SIGN': [getSign(params, SecretKey)]
    # }
    # # params = {'symbol': 'ethusdt',
    # #           'type': 'step0'}
    # postdata = urllib.parse.urlencode(params)
    # d = get(
    #     reactor,
    #     url="https://www.okex.com/api/v1/future_depth.do?" + postdata,
    #     headers=headers,
    # )

    # d = post(
    #     reactor,
    #     url="https://api.gateio.io/api2/1/private/buy",
    #     headers=headers,
    #     body=postdata
    # )
    # d = okexFuture.trade(('eth', 'usdt'), price="1", amount="2", tradeType="1", matchPrice="0", leverRate="10")

    pairs = ('eth', 'usdt')
    #d = okexFuture.getKLineLastMin(pairs, last=200)

    '''
    #test of bitfinex:
    pairs = ('eth', 'usdt')
    d = bitfinex.cancel(pairs,15172894785)
    d = bitfinex.getOrder(pairs,15172894785)
    d = bitfinex.sell(pairs,409,0.02)  #ps. fail to test buy() because money is not enough LOL
    d = bitfinex.getOrderBook(pairs)
    d = bitfinex.getBalance('usdt')
    '''

    def calc(KLines):
        # print(KLines[-3:])
        return (calcMAs(KLines), KLines[-2:], calcBolls(KLines)[-2:])

    d.addCallback(calc)
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
