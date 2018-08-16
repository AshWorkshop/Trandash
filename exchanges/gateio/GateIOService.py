from utils import Order
from exchanges.base import ExchangeService
from requestUtils.request import get, post
from .gateio_key import ApiKey, SecretKey
from hashlib import sha512 as encodeMethod
import hmac

from twisted.internet import reactor

import json

class GateIO(ExchangeService):

    def __init__(self, url, accessKey, secretKey):
        self.__url = url
        self.__accessKey = accessKey
        self.__secretKey = secretKey

    def getSymbol(self, pairs):
        return '_'.join(pairs).lower()

    def getPostBodyStr(self, body):
        bodyStr = ''
        for key, value in body.items():
            bodyStr += key + '=' + str(value) + '&'
        return bodyStr[:-1]

    def getSign(self, body):
        bSecretKey = bytes(self.__secretKey, encoding='utf8')
        bSign = bytes(body, encoding='utf8')

        mySign = hmac.new(bSecretKey, bSign, encodeMethod).hexdigest()
        return mySign

    def getCommonHeader(self):
        header = {
            'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36']
        }
        return header

    def getGetHeader(self):
        return self.getCommonHeader()

    def getPostHeader(self, body):
        header = self.getCommonHeader()
        newItems = {
            'Content-type': ['application/x-www-form-urlencoded'],
            'KEY': [self.__accessKey],
            'SIGN': [self.getSign(body)]
        }
        header.update(newItems)

        return header

    def getOrderBook(self, pairs):
        URL = "/api2/1/orderBook/"
        # print(self.__url)
        url = self.__url['data'] + URL + self.getSymbol(pairs)

        d = get(reactor, url, headers = self.getGetHeader())

        def handleBody(body):
            # print(body)
            data = json.loads(body)

            # print(data)

            flag = data['result']
            if type(flag) is str:
                flag = flag.upper() == 'TRUE'
            if not flag:
                return (False, data['code'], data['message'])

            bids = data['bids']
            asks = data['asks']
            asks.reverse()
            return [bids, asks] # (True, [bids, asks]) #TODO: handle error

        d.addCallback(handleBody)

        return d

    def getAddress(self, coin):
        URL = "/api2/1/private/depositAddress/"

        url = self.__url['balance'] + URL
        # print(url)

        prams = {'currency': coin.upper()}

        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # print(header)
        # print(prams)

        d = post(reactor, url, headers = header, body = body)

        def handleBody(body):
            data = json.loads(body)
            # print(data)

            flag = data['result']
            if type(flag) is str:
                flag = flag.upper() == 'TRUE'
            if not flag:
                return (False, data['code'], data['message'])

            addr = data['addr']
            return addr

        d.addCallback(handleBody)

        return d

    def getBalance(self, coin):
        d = self.getBalances()

        def handleBody(data):
            if isinstance(data, tuple) and not data[0]:
                return data
            elif coin.upper() in data:
                return data[coin.upper()]
            else:
                return 0

        d.addCallback(handleBody)

        return d

    def getBalances(self, coins=None):
        assert coins is None or isinstance(coins, (list, tuple) ), "type of 'coins' must be 'list' or 'tuple'"
        URL = "/api2/1/private/balances/"
        url = self.__url['balance'] + URL
        # print(url)

        prams = {}

        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # print(header)
        # print(prams)

        d = post(reactor, url, headers = header, body = body)

        def handleBody(body):
            data = json.loads(body)
            # print(data)

            flag = data['result']
            if type(flag) is str:
                flag = flag.upper() == 'TRUE'
            if not flag:
                return (False, data['code'], data['message'])

            if not data['available']:
                return None
            balances = {key: float(value) for key, value in data['available'].items()}

            if not coins:
                return balances
            else:
                return {coin: balances.get(coin.upper(), 0) for coin in coins}

        d.addCallback(handleBody)

        return d

    def buy(self, coinPair, price, amount):
        URL = "/api2/1/private/buy/"

        url = self.__url['balance'] + URL
        # print(url)

        prams = {
            'currencyPair': self.getSymbol(coinPair),
            'rate': price,
            'amount': amount
        }

        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # print(header)
        # print(prams)

        d = post(reactor, url, headers = header, body = body)

        def handleBody(body):
            # print(body)
            data = json.loads(body)
            # print(data)

            flag = data.get('result',False)
            if type(flag) is str:
                flag = flag.upper() == 'TRUE'
            if not flag:
                return (False, data['code'], data['message'])

            orederId = int(data['orderNumber'])
            return (True, orederId)

        d.addCallback(handleBody)
        d.addErrback(handleBody)

        return d

    def sell(self, coinPair, price, amount):
        URL = "/api2/1/private/sell/"

        url = self.__url['balance'] + URL
        # print(url)

        prams = {
            'currencyPair': self.getSymbol(coinPair),
            'rate': price,
            'amount': amount
        }
        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # print(header)
        # print(prams)

        d = post(reactor, url, headers = header, body = body)

        def handleBody(body):
            # print(body)
            data = json.loads(body)
            # print(data)

            flag = data.get('result',False)
            if type(flag) is str:
                flag = flag.upper() == 'TRUE'
            if not flag:
                return (False, data['code'], data['message'])

            orederId = int(data['orderNumber'])
            return (True,orederId)

        d.addCallback(handleBody)
        d.addErrback(handleBody)

        return d

    def getOrder(self, orderId, coinPair):
        URL = "/api2/1/private/getOrder/"

        url = self.__url['balance'] + URL
        # print(url)

        prams = {
            'orderNumber': orderId,
            'currencyPair': self.getSymbol(coinPair),
        }

        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # print(header)
        # print(prams)

        d = post(reactor, url, headers = header, body = body)

        def handleBody(body):
            # print(body)
            data = json.loads(body)

            # print(data)

            flag = data['result']
            if type(flag) is str:
                flag = flag.upper() == 'TRUE'
            if not flag:
                return (False, data['code'], data['message'])

            status = data['order']['status']
            if status == 'closed':
                status = 'done'

            order = Order(
                'gateio',
                orderId,
                data['order']['type'],
                float(data['order']['initialRate']),
                float(data['order']['initialAmount']),
                coinPair,
                status
            )
            # print(str(order))

            return (True, order)

        d.addCallback(handleBody)

        return d

    def getOpenOrders(self, coinPair = None):
        URL = "/api2/1/private/openOrders/"

        url = self.__url['balance'] + URL
        # print(url)

        if coinPair:
            currencyPair = self.getSymbol(coinPair)
        else:
            coinPair = ''

        prams = {
            'currencyPair': coinPair,
        }

        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # print(header)
        # print(prams)

        d = post(reactor, url, headers = header, body = body)

        def handleBody(body):
            # print(body)
            data = json.loads(body)

            # print(data)

            flag = data['result']
            if type(flag) is str:
                flag = flag.upper() == 'TRUE'
            if not flag:
                return (False, data['code'], data['message'])

            orders = []
            for orderData in data['orders']:
                order = Order(
                    'gateio',
                    orderData['orderNumber'],
                    orderData['type'],
                    float(orderData['initialRate']),
                    float(orderData['initialAmount']),
                    tuple(orderData['currencyPair'].split('_')),
                    'open'
                )
                # print(str(order))
                orders.append(order)
            return (True, orders)

        d.addCallback(handleBody)

        return d

    def cancelOrder(self, orderId, coinPair):
        URL = "/api2/1/private/cancelOrder/"

        url = self.__url['balance'] + URL
        # print(url)

        prams = {
            'orderNumber': orderId,
            'currencyPair': self.getSymbol(coinPair),
        }
        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # print(header)
        # print(prams)

        d = post(reactor, url, headers = header, body = body)

        def handleBody(body):
            # print(body)
            data = json.loads(body)
            # print(data)

            flag = data['result']
            if type(flag) is str:
                flag = flag.upper() == 'TRUE'
            if not flag:
                return (False, data['code'], data['message'])

            return (True, data['message'])

        d.addCallback(handleBody)

        return d

gateio = GateIO({'data':  'https://data.gateio.io',
                 'balance': 'https://api.gateio.io'  },
                 ApiKey, SecretKey)
