from exchanges.base import ExchangeService
from request import get
from .bitfinex_key import ApiKey, SecretKey

from twisted.internet import reactor

import json
import time

class Bitfinex(ExchangeService):

    def __init__(self, url, accessKey, secretKey):
        self.__url = url
        self.__accessKey = accessKey
        self.__secretKey = secretKey

    def getSymbol(self, pairs):
        coin, money = pairs
        if money.upper() == 'USDT':
            money = 'USD'
        return ''.join((coin, money)).upper()

    def getOrderBook(self, pairs):
        URL = "/v1/book/"
        # print(self.__url)
        url = self.__url + URL + self.getSymbol(pairs)
        # print(url)

        d = get(reactor, url)

        def handleBody(body):
            # print(body)
            data = json.loads(body)
            # print(data)

            try:
                rawBids = data['bids']
                rawAsks = data['asks']
            except KeyError:
                rawBids = []
                rawAsks = []
                if 'error' in data:
                    err = data['error']
                    if err == 'ERR_RATE_LIMIT':
                        time.sleep(1)

            bids = []
            asks = []

            for bid in rawBids:
                bids.append([bid['price'], bid['amount']])

            for ask in rawAsks:
                asks.append([ask['price'], ask['amount']])

            return [bids, asks]

        d.addCallback(handleBody)

        return d

bitfinex = Bitfinex('https://api.bitfinex.com', ApiKey, SecretKey)
