from exchanges.base import ExchangeService
from requestUtils.request import get, post
from .bitfinex_key import ApiKey, SecretKey
from .HttpUtil import getPostHeaders
from utils import Order

from twisted.internet import reactor

import json
import time
import urllib

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
        headers = {'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36']}
        d = get(reactor, url, headers=headers)

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
                    print(err)
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

    def getBalance(self, coin):
        URL = "/v1/balances"
        # print(self.__url)
        url = self.__url + URL
        # print(url)
        headers = getPostHeaders(url, URL)
        d = post(reactor, url, headers=headers)
        if coin == 'usdt':
            coin = 'usd'

        def handleBody(body):
            # print(body)
            data = json.loads(body)
            # print(data)
            balance = 0.0
            for b in data:
                try:
                    b_type = b['type']
                    b_currency = b['currency']
                    b_available = b['available']
                except KeyError:
                    b_type = ''
                    b_currency = ''
                    b_available = 0.0
                    if 'error' in data:
                        err = data['error']
                        print(err)
                        if err == 'ERR_RATE_LIMIT':
                            time.sleep(1)
                if b_type == 'exchange':
                    # print(b)
                    if b_currency == coin:
                        # print(b['currency'])
                        balance = float(b_available)  #balance that is available to trade
                        break
            return balance

        d.addCallback(handleBody)

        return d

    def getBalances(self, coins):
        URL = "/v1/balances"
        # print(self.__url)
        url = self.__url + URL
        # print(url)
        headers = getPostHeaders(url, URL)
        d = post(reactor, url, headers=headers)
        for coin in coins:
            if coin == 'usdt':
                coin = 'usd'

        def handleBody(body):
            # print(body)
            data = json.loads(body)
            # print(data)
            balances = dict()
            for b in data:
                try:
                    b_type = b['type']
                    b_currency = b['currency']
                    b_available = b['available']
                except KeyError:
                    b_type = ''
                    b_currency = ''
                    b_available = 0.0
                    if 'error' in data:
                        err = data['error']
                        print(err)
                        if err == 'ERR_RATE_LIMIT':
                            time.sleep(1)
                if b_type == 'exchange':
                    # print(b)
                    if b_currency in coins:
                        # print(b['currency'])
                        balances[coin] = float(b_available)  #balance that is available to trade

            if balances == {}:
                return None
            return balances

        d.addCallback(handleBody)

        return d

    def buy(self, pairs, price, amount):
        URL = "/v1/order/new"
        # print(self.__url)
        url = self.__url + URL
        # print(url)
        symbol = self.getSymbol(pairs)
        params = {
            'symbol': symbol,
            'amount': str(amount),
            'price': str(price),
            'side': 'buy',
            'type': 'exchange limit',
            'exchange': 'bitfinex'
            }
        headers = getPostHeaders(url, URL, payload_params=params)
        d = post(reactor, url, headers=headers)

        def handleBody(body):
            # print(body)
            data = json.loads(body)
            # print(data)

            try:
                order_id = data['order_id']
            except KeyError:
                order_id = '0'
                if 'error' in data:
                    err = data['error']
                    print(err)
                    if err == 'ERR_RATE_LIMIT':
                        time.sleep(1)

            return int(order_id)

        d.addCallback(handleBody)

        return d

    def sell(self, pairs, price, amount):
        URL = "/v1/order/new"
        # print(self.__url)
        url = self.__url + URL
        # print(url)
        symbol = self.getSymbol(pairs)
        params = {
            'symbol': symbol,
            'amount': str(amount),
            'price': str(price),
            'side': 'sell',
            'type': 'exchange limit',
            'exchange': 'bitfinex'
            }
        headers = getPostHeaders(url, URL, payload_params=params)
        d = post(reactor, url, headers=headers)

        def handleBody(body):
            # print(body)
            data = json.loads(body)
            # print(data)

            try:
                order_id = data['order_id']
            except KeyError:
                order_id = '0'
                if 'error' in data:
                    err = data['error']
                    print(err)
                    if err == 'ERR_RATE_LIMIT':
                        time.sleep(1)

            return int(order_id)

        d.addCallback(handleBody)

        return d

    def getOrder(self, pairs, orderId):
        URL = "/v1/order/status"
        # print(self.__url)
        url = self.__url + URL
        # print(url)
        symbol = self.getSymbol(pairs)
        params = {}
        params['order_id'] = orderId
        headers = getPostHeaders(url, URL, payload_params=params)
        d = post(reactor, url, headers=headers)

        def handleBody(body):
            # print(body)
            data = json.loads(body)
            # print(data)

            try:
                side = data['side']
                price = data['price']
                amount = data['original_amount']
                is_cancelled = data['is_cancelled']
                is_live = data['is_live']
            except KeyError:
                side = ''
                price = '0'
                amount = '0'
                is_cancelled = False
                is_live = False
                if 'error' in data:
                    err = data['error']
                    print(err)
                    if err == 'ERR_RATE_LIMIT':
                        time.sleep(1)

            status = 'open'
            if 'error' in data:    #若有错误，status置为'error'
                status = 'error'
            elif is_cancelled:
                status = 'cancelled'
            elif not is_live:      #若没有被取消，并且不能继续被填充（not live），
                status = 'done'            #则表示交易已完成（done）

            return Order(
                'bitfinex',
                orderId,
                side,
                float(price),
                float(amount),
                symbol,
                status
            )

        d.addCallback(handleBody)

        return d

    def cancel(self, pairs, orderId):
        URL = "/v1/order/cancel"
        # print(self.__url)
        url = self.__url + URL
        # print(url)
        symbol = self.getSymbol(pairs)
        params = {}
        params['order_id'] = orderId
        headers = getPostHeaders(url, URL, payload_params=params)
        d = post(reactor, url, headers=headers)

        def handleBody(body):
            # print(body)
            data = json.loads(body)
            # print(data)

            try:
                is_cancelled = data['is_cancelled']
            except KeyError:
                is_cancelled = False
                if 'error' in data:
                    err = data['error']
                    print(err)
                    if err == 'ERR_RATE_LIMIT':
                        time.sleep(1)
                return (False, data)
            if is_cancelled:
                return(True, data)

        d.addCallback(handleBody)

        return d

    def getOrderHistory(self, pairs, givenTime=float(time.time())):
        #View your latest inactive orders. Limited to last 3 days and 1 request per minute.
        URL = "/v1/orders/hist"
        # print(self.__url)
        url = self.__url + URL
        # print(url)
        symbol = self.getSymbol(pairs)
        headers = getPostHeaders(url, URL)
        d = post(reactor, url, headers=headers)

        def handleBody(body):
            # print(body)
            data = json.loads(body)
            # print(data)
            orderList = []

            if not isinstance(data, list):
                return None

            for order in data:
                try:
                    timestamp = order['timestamp']
                    if float(timestamp) >= givenTime:
                        status = 'open'
                        if order['is_cancelled']:
                            status = 'cancelled'
                        elif not order['is_live']:      #若没有被取消，并且不能继续被填充（not live），
                            status = 'done'             #则表示交易已完成（done）
                        orderList.append({
                            'orderId': order['id'],
                            'timestamp': timestamp,     #返回的字典中添加了时间戳信息
                            'type': order['side'],
                            'iniPrice': float(order['price']),
                            'initAmount': float(order['original_amount']),
                            'coinPair': symbol,
                            'status': status
                            })
                except KeyError:
                    if 'error' in data:
                        err = data['error']
                        print(err)
                        if err == 'ERR_RATE_LIMIT':
                            time.sleep(1)

            return orderList

        d.addCallback(handleBody)

        return d

    def getTicker(self, pairs):
        URL = "/v2/ticker/"
        symbol = self.getSymbol(pairs)
        url = self.__url + URL + 't' + symbol
        headers = {'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36']}
        d = get(
            reactor,
            url=url,
            headers=headers
        )
        def handleBody(body):
            data = json.loads(body)
            if isinstance(data, list) and len(data) == 10:
                return data
            else:
                print(data)
                return None

        d.addCallback(handleBody)

        return d

    def getKLine(self, pairs, timeFrame='1m', start=None, end=None, sort=-1, limit=None):
        URL = "/v2/candles/trade:"
        symbol = self.getSymbol(pairs)
        url = self.__url + URL + timeFrame + ':t' + symbol + '/hist'
        params = {
            'start': start,
            'sort': sort
        }
        if end:
            params['end'] = end
        if limit:
            parmas['limit'] = limit
        postdata = urllib.parse.urlencode(params)
        headers = {'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36']}
        d = get(
            reactor,
            url=url + '?' + postdata,
            headers=headers
        )
        def handleBody(body):
            data = json.loads(body)
            result = []
            if isinstance(data, list):
                for kline in data:
                    try:
                        t, o, c, h, l, v = kline
                        result.append([t, o, h, l, c, v, 0])
                    except Exception as err:
                        print(err)
                        print(kline)
            return result
        d.addCallback(handleBody)

        return d

    def getKLineLastMin(self, pairs, last=0):
        t = int(round(time.time() * 1000))
        sincet = t - last * 60 * 1100
        d = self.getKLine(pairs, start=sincet)

        def handleList(KLines):
            result = []
            if len(KLines) < last:
                return None
            try:
                result = KLines[-last:]
            except Exception as err:
                print(err)
                return None
            return result
        d.addCallback(handleList)

        return d

bitfinex = Bitfinex(
    'https://api.bitfinex.com',
    ApiKey,
    SecretKey
    )
