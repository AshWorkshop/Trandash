from exchanges.base import ExchangeService
from request import get
from .gateio_key import ApiKey, SecretKey

from twisted.internet import reactor

import json

class GateIO(ExchangeService):

    def __init__(self, url, accessKey, secretKey):
        self.__url = url
        self.__accessKey = accessKey
        self.__secretKey = secretKey

    def getSymbol(self, pairs):
        return '_'.join(pairs).upper()

    def getOrderBook(self, pairs):
        URL = "/api2/1/orderBook/"
        # print(self.__url)
        url = self.__url + URL + self.getSymbol(pairs)
        # print(url)
        headers = {'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36']}
        d = get(reactor, url, headers=headers)

        def handleBody(body):
            # print(body)
            data = json.loads(body)
            bids = data['bids']
            asks = data['asks']
            return [bids, asks]

        d.addCallback(handleBody)

        return d

gateio = GateIO('https://data.gateio.io', ApiKey, SecretKey)
