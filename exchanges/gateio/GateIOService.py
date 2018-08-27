from utils import Order
from exchanges.base import ExchangeService
from requestUtils.request import get, post
from .gateio_key import ApiKey, SecretKey
from hashlib import sha512 as encodeMethod
import hmac

from twisted.internet import reactor, defer
from twisted.python.failure import Failure
from twisted.logger import Logger

import json

class GateIO(ExchangeService):
    log = Logger

    def defaultErrhandler(self, failure):
        self.log.error(failure)

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
        # self.log.debug("{url}", url=self.__url)
        url = self.__url['data'] + URL + self.getSymbol(pairs)

        d = get(reactor, url, headers = self.getGetHeader())

        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)

            # self.log.debug("{data}", data=data)

            flag = data['result']
            if isinstance(flag, str):
                flag = flag.upper() == 'TRUE'
            assert flag, f"{data.get('message', 'unknown error')}, ErrorCode: {data.get('code', 'unknown')}"

            bids = [list(map(float, bid)) for bid in data['bids']]
            asks = [list(map(float, ask)) for ask in data['asks']]
            asks.reverse()
            return [bids, asks]

        d.addCallback(handleBody)
        d.addErrback(self.defaultErrhandler)

        return d

    def getAddress(self, coin):
        URL = "/api2/1/private/depositAddress/"

        url = self.__url['balance'] + URL
        # self.log.debug("{url}", url=url)

        prams = {'currency': coin.upper()}

        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # self.log.debug("{header}", header=header)
        # self.log.debug("{prams}", prams=prams)

        d = post(reactor, url, headers = header, body = body)

        def handleBody(body):
            data = json.loads(body)
            # self.log.debug("{data}", data=data)

            flag = data['result']
            if isinstance(flag, str):
                flag = flag.upper() == 'TRUE'
            assert flag, f"{data.get('message', 'unknown error')}, ErrorCode: {data.get('code', 'unknown')}"

            addr = data['addr']
            return addr

        d.addCallback(handleBody)
        d.addErrback(self.defaultErrhandler)

        return d

    def getBalance(self, coin):
        d = self.getBalances()

        def handleBody(data):
            if coin.upper() in data:
                return data[coin.upper()]
            else:
                return 0

        d.addCallback(handleBody)

        return d

    def getBalances(self, coins=None):
        assert coins is None or isinstance(coins, (list, tuple) ), "type of 'coins' must be 'list' or 'tuple'"
        URL = "/api2/1/private/balances/"
        url = self.__url['balance'] + URL
        # self.log.debug("{url}", url=url)

        prams = {}

        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # self.log.debug("{header}", header=header)
        # self.log.debug("{prams}", prams=prams)

        d = post(reactor, url, headers = header, body = body)

        def handleBody(body):
            data = json.loads(body)
            # self.log.debug("{data}", data=data)

            flag = data['result']
            if isinstance(flag, str):
                flag = flag.upper() == 'TRUE'
            assert flag, f"{data.get('message', 'unknown error')}, ErrorCode: {data.get('code', 'unknown')}"

            if not data['available']:
                return {}
            balances = {key: float(value) for key, value in data['available'].items()}

            if not coins:
                return balances
            else:
                return {coin: balances.get(coin.upper(), 0) for coin in coins}

        d.addCallback(handleBody)
        d.addErrback(self.defaultErrhandler)

        return d

    def buy(self, coinPair, price, amount):
        URL = "/api2/1/private/buy/"

        url = self.__url['balance'] + URL
        # self.log.debug("{url}", url=url)

        prams = {
            'currencyPair': self.getSymbol(coinPair),
            'rate': price,
            'amount': amount
        }

        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # self.log.debug("{header}", header=header)
        # self.log.debug("{prams}", prams=prams)

        d = post(reactor, url, headers = header, body = body)

        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)
            # self.log.debug("{data}", data=data)

            flag = data['result']
            if isinstance(flag, str):
                flag = flag.upper() == 'TRUE'
            assert flag, f"{data.get('message', 'unknown error')}, ErrorCode: {data.get('code', 'unknown')}"

            orederId = int(data['orderNumber'])
            return orederId

        d.addCallback(handleBody)
        d.addErrback(self.defaultErrhandler)

        return d

    def sell(self, coinPair, price, amount):
        URL = "/api2/1/private/sell/"

        url = self.__url['balance'] + URL
        # self.log.debug("{url}", url=url)

        prams = {
            'currencyPair': self.getSymbol(coinPair),
            'rate': price,
            'amount': amount
        }
        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # self.log.debug("{header}", header=header)
        # self.log.debug("{prams}", prams=prams)

        d = post(reactor, url, headers = header, body = body)

        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)
            # self.log.debug("{data}", data=data)

            flag = data['result']
            if isinstance(flag, str):
                flag = flag.upper() == 'TRUE'
            assert flag, f"{data.get('message', 'unknown error')}, ErrorCode: {data.get('code', 'unknown')}"

            orederId = int(data['orderNumber'])
            return orederId

        d.addCallback(handleBody)
        d.addErrback(self.defaultErrhandler)

        return d

    def getOrder(self, orderId, coinPair):
        URL = "/api2/1/private/getOrder/"

        url = self.__url['balance'] + URL
        # self.log.debug("{url}", url=url)

        prams = {
            'orderNumber': orderId,
            'currencyPair': self.getSymbol(coinPair),
        }

        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # self.log.debug("{header}", header=header)
        # self.log.debug("{prams}", prams=prams)

        d = post(reactor, url, headers = header, body = body)

        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)

            # self.log.debug("{data}", data=data)

            flag = data['result']
            if isinstance(flag, str):
                flag = flag.upper() == 'TRUE'
            assert flag, f"{data.get('message', 'unknown error')}, ErrorCode: {data.get('code', 'unknown')}"

            status = data['order']['status']
            if status == 'closed':
                status = 'done'

            order = {
                'orderId': orderId,
                'type': data['order']['type'],
                'initPrice': float(data['order']['initialRate']),
                'initAmount': float(data['order']['initialAmount']),
                'coinPair': coinPair,
                'status': status
            }
            # self.log.debug("{order!s}", order=order)

            return order

        d.addCallback(handleBody)
        d.addErrback(self.defaultErrhandler)

        return d

    def getOrders(self, coinPair):
        URLdone = "/api2/1/private/tradeHistory/"
        URLopen = "/api2/1/private/openOrders/"

        urlDone = self.__url['balance'] + URLdone
        urlOpen = self.__url['balance'] + URLopen
        # self.log.debug("{url}", url=url)

        if coinPair:
            currencyPair = self.getSymbol(coinPair)
        else:
            currencyPair = ''

        prams = {
            'currencyPair': currencyPair,
        }

        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # self.log.debug("{header}", header=header)
        # self.log.debug("{prams}", prams=prams)

        dDone = post(reactor, urlDone, headers = header, body = body)
        dOpen = post(reactor, urlOpen, headers = header, body = body)
        
        d = defer.DeferredList([dDone, dOpen], consumeErrors=True)

        def handleBody(res):
            # self.log.debug("{res}", res=res)
            for state, err in res:
                if not state:
                    raise err
            
            (_, dataDone), (_, dataOpen) = res
            dataDone, dataOpen = json.loads(dataDone), json.loads(dataOpen)
            # self.log.debug("{dataDone}{dataOpen}", dataDone=dataDone, dataOpen=dataOpen)

            for data in [dataDone, dataOpen]:
                flag = data['result']
                if isinstance(flag, str):
                    flag = flag.upper() == 'TRUE'
                assert flag, f"{data.get('message', 'unknown error')}, ErrorCode: {data.get('code', 'unknown')}"

            orders = []
            for orderData in dataOpen['orders']:
                order = {
                    'orderId': orderData['orderNumber'],
                    'type': orderData['type'],
                    'initPrice': float(orderData['initialRate']),
                    'initAmount': float(orderData['initialAmount']),
                    'coinPair': tuple(orderData['currencyPair'].split('_')),
                    'status': 'open'
                }
                # self.log.debug("{order!s}", order=order)
                orders.append(order)
            for orderData in dataDone['trades']:
                order = {
                    'orderId': orderData['orderNumber'],
                    'type': orderData['type'],
                    'initPrice': float(orderData['rate']),
                    'initAmount': float(orderData['amount']),
                    'coinPair': tuple(orderData['pair'].split('_')),
                    'status': 'done'
                }
                # self.log.debug("{order!s}", order=order)
                orders.append(order)
            return orders

        d.addCallback(handleBody)
        d.addErrback(self.defaultErrhandler)

        return d

    def cancel(self, orderId, coinPair):
        URL = "/api2/1/private/cancelOrder/"

        url = self.__url['balance'] + URL
        # self.log.debug("{url}", url=url)

        prams = {
            'orderNumber': orderId,
            'currencyPair': self.getSymbol(coinPair),
        }
        body = self.getPostBodyStr(prams)
        header = self.getPostHeader(body)
        # self.log.debug("{header}", header=header)
        # self.log.debug("{prams}", prams=prams)

        d = post(reactor, url, headers = header, body = body)

        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)
            # self.log.debug("{data}", data=data)

            flag = data['result']
            if isinstance(flag, str):
                flag = flag.upper() == 'TRUE'
            assert flag, f"{data.get('message', 'unknown error')}, ErrorCode: {data.get('code', 'unknown')}"

            return True
            
        def errhandler(failure):
            self.log.error("{failure}", failure=failure)
            return False

        d.addCallback(handleBody)
        d.addErrback(errhandler)

        return d

gateio = GateIO({'data':  'https://data.gateio.io',
                 'balance': 'https://api.gateio.io'  },
                 ApiKey, SecretKey)
