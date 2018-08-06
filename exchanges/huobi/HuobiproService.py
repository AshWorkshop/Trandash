from exchanges.base import ExchangeService
from request import get
from .huobipro_key import AccessKey, SecretKey

from twisted.internet import reactor

import json


class Huobipro(ExchangeService):

    def __init__(self, url, accessKey, secretKey):
        self.__url = url
        self.__accessKey = accessKey
        self.__secretKey = secretKey

    def getSymbol(self, pairs):
        return ''.join(pairs).upper()

    def getOrderBook(self, pairs):
        URL = "/market/depth/"

        url = self.__url + URL + self.getSymbol(pairs)

        d = get(reactor,url)

        def handleBody(body):
            print(body)
            data = body
            #data = json.load(body)
            print(data)
            bids = data['bids']
            asks = data['asks']

        d.addCallback(handleBody)
        #print(b)
        return d

huobi = Huobipro('https://api.huobi.pro' , AccessKey, SecretKey)
