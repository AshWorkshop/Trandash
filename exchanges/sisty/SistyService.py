from utils import Order
from exchanges.base import ExchangeService
from requestUtils.request import get, post
from exchanges.sisty.sisty_key import MD5Key
from twisted.python.failure import Failure

import hashlib
import urllib
import time

from twisted.internet import reactor
from twisted.logger import Logger

import json

def httpGet(url, resource, params, callback=None, errback=None):
    headers = {
        "Content-type": ["application/x-www-form-urlencoded"],
        'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'],
    }
    postdata = urllib.parse.urlencode(params)
    # print(url + resource + '?' + postdata)
    d = get(
        reactor,
        url=url + resource + '?' + postdata,
        headers=headers
    )
    if callback:
        d.addCallback(callback)
    if errback:
        d.addErrback(errback)

    return d

def httpPost(url, resource, params, callback=None, errback=None):
    headers = {
        "Content-type": ["application/x-www-form-urlencoded"],
        'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'],
    }
    postdata = urllib.parse.urlencode(params)
    # print(url + resource)
    # print(postdata)
    d = post(
        reactor,
        url=url + resource,
        headers=headers,
        body=postdata
    )
    if callback:
        d.addCallback(callback)
    if errback:
        d.addErrback(errback)

    return d

def getSign(*args):
    data = ''
    for arg in args:
        assert isinstance(arg, str)
        data += arg
    return hashlib.md5(data.encode("utf8")).hexdigest().upper()



class Sisty(ExchangeService):
    log = Logger()

    def __init__(self, url, md5Key, userId, secret):
        self.__url = url
        self.__md5Key = md5Key
        self.__userId = userId
        self.__secret = secret

    def getSymbol(self, pairs):
        coin, money = pairs
        return '_'.join((coin, money)).lower()

    def ebFailed(self, failure):
        self.log.error("{failure}", failure=failure)
        return failure

    def getTicker(self, pairs):
        URL = "/trademarket/v1/api/ticker"

        params = {
            'market': self.getSymbol(pairs),
        }

        def handleBody(body):
            data = json.loads(body)
            assert 'ticker' in data
            return data['ticker']

        return httpGet(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)


    def getOrderBook(self, pairs):
        URL = "/trademarket/v1/api/depth"
        # self.log.debug("{url}", url=self.__url)

        params = {
            'market': self.getSymbol(pairs),
        }

        def handleBody(body):
            data = json.loads(body)
            assert 'bids' in data and 'asks' in data
            bids = data['bids']
            asks = data['asks']
            return [bids, asks]

        return httpGet(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

    def trade(self, pairs, price, amount, tradeType):
        URL = "/tradeOpen/v2/apiAddEntrustV2Robot"

        cipherText = getSign(self.__userId, pairs[0], self.__secret, pairs[1], self.__md5Key)
        # self.log.debug("{cipherText}{key}", cipherText=cipherText, key=self.__md5Key)
        params = {
            'coinName': pairs[0],
            'payCoinName': pairs[1],
            'amount': amount,
            'price': price,
            'type': tradeType, # 1: buy, 2: sell
            'cipherText': cipherText,
            'secret': self.__secret,
            'userId': self.__userId
        }


        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)
            assert 'code' in data
            if data['code'] == 0:
                return data
            else:
                self.log.error('errorCode: {code}', code=data['code'])
                return None

        return httpPost(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

    def cancel(self, pairs, orderId=""):
        URL = "/tradeOpen/v2/apiCancelEntrustV2Robot"
        cipherText = getSign(self.__userId, orderId, self.__md5Key)
        params = {
            'entrustId': orderId,
            'cipherText': cipherText,
            'userId': self.__userId
        }


        def handleBody(body):
            data = json.loads(body)
            assert 'code' in data
            if data['code'] == 0:
                return True
            else:
                self.log.debug("{data}", data=data)
                return False

        return httpPost(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

    def cancelAll(self, pairs, cancelType, isAll=False):
        """
        isAll: True: cancel all pairs, False: cancel given pairs
        cancelType: 0: all bids and asks, 1: all bids, 2: all asks
        """
        URL = "/tradeOpen/v1/batchCancel"
        cipherText = getSign(self.__userId, pairs[0], pairs[1], self.__md5Key)
        # self.log.debug("{cipherText}{key}", cipherText=cipherText, key=self.__md5Key)
        cancelType = bytes(cancelType)
        params = {
            'coinName': pairs[0],
            'payCoinName': pairs[1],
            'isAll': isAll, # True: cancel all pairs, False: cancel given pairs
            'type': cancelType, # 0: all bids and asks, 1: all bids, 2: all asks
            'cipherText': cipherText,
            'userId': self.__userId
        }


        def handleBody(body):
            data = json.loads(body)
            assert 'model' in data
            if data['model'] == 0:
                return True
            else:
                self.log.debug("{data}", data=data)
                return False

        return httpPost(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

    def getOrder(self, pairs, orderId=""):
        URL = "/tradeOpen/v2/selectEntrustById"
        cipherText = getSign(self.__userId, orderId, self.__md5Key)
        params = {
            'entrustId': orderId,
            'cipherText': cipherText,
            'userId': self.__userId
        }

        def handleBody(body):
            data = json.loads(body)
            assert 'code' in data
            if data['code'] == 0:
                return data
            else:
                self.log.error('errorCode: {code}', code=data['code'])
                return None

        return httpPost(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)


    def getOrders(self, pairs, tradeType, status, pageNum=1, pageSize=100):
        URL = "/tradeOpen/v2/apiSelectEntrustV2Robot"
        cipherText = getSign(self.__userId, self.__md5Key)
        params = {
            'coinName': pairs[0],
            'payCoinName': pairs[1],
            'type': tradeType,
            'status': status,
            'pageNum': pageNum,
            'pageSize': pageSize,
            'cipherText': cipherText,
            'userId': self.__userId
        }

        def handleBody(body):
            data = json.loads(body)
            # self.log.debug("{data}", data=data)
            assert 'code' in data
            if data['code'] == 0:
                return data
            else:
                self.log.error('errorCode: {code}', code=data['code'])
                return None

        return httpPost(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

    def getUserInfo(self):
        URL = "/tradeOpen/v3/getUserCapitalInfoRobot"
        cipherText = getSign(self.__userId, self.__md5Key)
        params = {
            'cipherText': cipherText,
            'userId': self.__userId
        }

        def handleBody(body):
            data = json.loads(body)
            assert 'code' in data
            if data['code'] == 0:
                return data
            else:
                return None

        return httpPost(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

sisty = Sisty('http://47.75.31.125/app', MD5Key, '222', '12345678')
