from utils import Order
from exchanges.base import ExchangeService
from request import get, post
from .okex_key import ApiKey, SecretKey

import hashlib
import urllib
import time

from twisted.internet import reactor

import json

def buildMySign(params,secretKey):
    sign = ''
    for key in sorted(params.keys()):
        sign += key + '=' + str(params[key]) +'&'
    data = sign+'secret_key='+secretKey
    return  hashlib.md5(data.encode("utf8")).hexdigest().upper()

def httpGet(url, resource, params, callback=None, errback=None):
    headers = {
        "Content-type": ["application/x-www-form-urlencoded"],
        'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'],
    }
    postdata = urllib.parse.urlencode(params)
    print(url + resource + '?' + postdata)
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
    print(url + resource)
    print(postdata)
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



class OKexFuture(ExchangeService):

    def __init__(self, url, accessKey, secretKey):
        self.__url = url
        self.__accessKey = accessKey
        self.__secretKey = secretKey

    def getSymbol(self, pairs):
        coin, money = pairs
        if money.lower() == 'usdt':
            money = 'usd'
        return '_'.join((coin, money)).lower()

    def getOrderBook(self, pairs):
        URL = "/api/v1/future_depth.do"
        # print(self.__url)
        
        params = {
            'symbol': self.getSymbol(pairs),
            'contract_type': 'this_week',
        }

        def handleBody(body):
            data = json.loads(body)
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            asks.reverse()
            return [bids, asks]

        d = httpGet(self.__url, URL, params, callback=handleBody)

        return d

    def getPosition(self, pairs):
        URL = "/api/v1/future_position_4fix"

        params = {
            'symbol': self.getSymbol(pairs),
            'contract_type': 'this_week',
            'api_key': self.__accessKey,
        }
        sign = buildMySign(params, self.__secretKey)
        params['sign'] = sign

        def handleBody(body):
            return body

        d = httpPost(self.__url, URL, params, callback=handleBody)

        return d

    def trade(self, pairs, contractType="this_week", price="", amount="", tradeType="", matchPrice="", leverRate=""):
        URL = "/api/v1/future_trade.do"
        params = {
            'api_key': self.__accessKey,
            'symbol': self.getSymbol(pairs),
            'contract_type': contractType,
            'amount': amount,
            'type': tradeType,
            'match_price': matchPrice,
            'lever_rate': leverRate
        }

        if price:
            params['price'] = price

        sign = buildMySign(params, self.__secretKey)
        params['sign'] = sign

        def handleBody(body):
            data = json.loads(body)
            orderId = None
            if data.get('result', False):
                orderId = data['order_id']
            return orderId

        d = httpPost(self.__url, URL, params, callback=handleBody)
        return d

    def cancle(self, pairs, contractType="this_week", orderId=""):
        URL = "/api/v1/future_cancel"
        params = {
            "api_key": self.__accessKey,
            "symbol": self.getSymbol(pairs),
            "order_id": orderId,
            "contract_type": contractType
        }
        sign = buildMySign(params, self.__secretKey)
        params['sign'] = sign

        def handleBody(body):
            data = json.loads(body)
            if data.get('result', False):
                return (True, orderId)
            else:
                print(data)
                return (False, data.get("error", ""))

        d = httpPost(self.__url, URL, params, callback=handleBody)

        return d

    def getOrder(self, pairs, contractType='this_week', orderId="", status=""):
        URL = "/api/v1/future_order_info"
        params = {
            "api_key": self.__accessKey,
            "symbol": self.getSymbol(pairs),
            "order_id": orderId,
            "contract_type": contractType
        }
        if status:
            params['status'] = status
        sign = buildMySign(params, self.__secretKey)
        params['sign'] = sign

        def handleBody(body):
            data = json.loads(body)
            return data
        
        d = httpPost(self.__url, URL, params, callback=handleBody)
        return d

okexFuture = OKexFuture(
    'https://www.okex.com',
    ApiKey,
    SecretKey
)
