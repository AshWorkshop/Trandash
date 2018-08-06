from exchanges.base import ExchangeService
from request import get
from .huobipro_key import AccessKey, SecretKey

from twisted.internet import reactor

import json
import urllib.parse

class Huobipro(ExchangeService):

    def __init__(self, url, accessKey, secretKey):
        self.__url = url
        self.__accessKey = accessKey
        self.__secretKey = secretKey

    def getSymbol(self, pairs):
        return ''.join(pairs)

    def toGradeStr(self,grade):
        return ('step'+str(grade))

    def getOrderBook(self, pairs,grade=0):
        URL = "/market/depth?"

        params={'symbol':self.getSymbol(pairs),
                'type':self.toGradeStr(grade),
        }
        postdata = urllib.parse.urlencode(params)
        url = self.__url + URL + postdata

        headers = {
            "Content-type": ["application/x-www-form-urlencoded"],
            'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'],
        }
        d = get(reactor,url,headers = headers)

        def handleBody(body):
            #print(body)
            data = json.loads(body)
            #print(data)
            bids = data['tick']['bids']
            asks = data['tick']['asks']
            return [bids, asks]

        d.addCallback(handleBody)
        #print(b)
        return d

huobi = Huobipro('https://api.huobi.pro' , AccessKey, SecretKey)
