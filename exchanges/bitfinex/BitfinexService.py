from exchanges.base import ExchangeService
from requestUtils.request import get, post
from .bitfinex_key import ApiKey, SecretKey
from .HttpUtil import getPostHeaders
from utils import Order

from twisted.internet import reactor
from twisted.logger import Logger
from twisted.python.failure import Failure

import json
import time
import urllib

class Bitfinex(ExchangeService):
    log = Logger()

    def defaultErrhandler(self, failure):
        self.log.error(failure)
        # time.sleep(1)
        return None

    def ratelimitErrhandler(self, failure):
        self.log.error(failure)
        time.sleep(1)
        return None

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
        #ratelimit: 60 req/min
        URL = "/v1/book/"
        # self.log.debug("{url}", url=self.__url)
        url = self.__url + URL + self.getSymbol(pairs)
        # self.log.debug("{url}", url=url)
        headers = {'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36']}
        d = get(reactor, url, headers=headers)

        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)
            # self.log.debug("{data}", data=data)

            assert 'bids' in data, str(data)
            rawBids = data['bids']
            rawAsks = data['asks']
            # except KeyError:
            #     rawBids = []
            #     rawAsks = []
            #     if 'error' in data:
            #         err = data['error']
            #         self.log.error('{err} from getOrderBook()', err=err)
            #         if err == 'ERR_RATE_LIMIT':
            #             time.sleep(1)

            bids = []
            asks = []

            for bid in rawBids:
                bids.append( [float(bid['price']), float(bid['amount'])] )

            for ask in rawAsks:
                asks.append( [float(ask['price']), float(ask['amount'])] )

            return [bids, asks]

        d.addCallback(handleBody)
        d.addErrback(self.ratelimitErrhandler)

        return d

    def getBalance(self, coin):
        #ratelimit: 20 req/min
        URL = "/v1/balances"
        # self.log.debug("{url}", url=self.__url)
        url = self.__url + URL
        # self.log.debug("{url}", url=url)
        headers = getPostHeaders(url, URL)
        d = post(reactor, url, headers=headers)
        if coin == 'usdt':
            coin = 'usd'

        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)
            self.log.debug("{data}", data=data)
            balance = 0.0
            assert isinstance(data, list), str(data)

            for b in data:
                b_type = b['type']
                b_currency = b['currency']
                b_available = b['available']
                # except Exception as e:
                #     b_type = ''
                #     b_currency = ''
                #     b_available = 0.0
                #     if 'error' in data:
                #         err = data['error']
                #         self.log.error('{err} from getBalance()', err=err)
                #         if err == 'ERR_RATE_LIMIT':
                #             time.sleep(1)
                if b_type == 'exchange':
                    # self.log.debug("{b}", b=b)
                    if b_currency == coin:
                        # self.log.debug("{currency}", currency=b['currency'])
                        balance = float(b_available)  #balance that is available to trade
                        break
            return balance

        d.addCallback(handleBody)
        d.addErrback(self.ratelimitErrhandler)

        return d

    def getBalances(self, coins):
        #ratelimit: 20 req/min
        URL = "/v1/balances"
        # self.log.debug("{url}", url=self.__url)
        url = self.__url + URL
        # self.log.debug("{url}", url=url)
        headers = getPostHeaders(url, URL)
        d = post(reactor, url, headers=headers)
        for i in range(len(coins)):
            if coins[i] == 'usdt':
                coins[i] = 'usd'

        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)
            # self.log.debug("{data}", data=data)
            balances = dict()
            assert isinstance(data, list), str(data)
            
            for b in data:
                b_type = b['type']
                b_currency = b['currency']
                b_available = b['available']
                # except Exception as e:
                #     b_type = ''
                #     b_currency = ''
                #     b_available = 0.0
                #     if 'error' in data:
                #         err = data['error']
                #         self.log.debug('{err} from getBalances()', err=err)
                #         if err == 'ERR_RATE_LIMIT':
                #             time.sleep(1)
                if b_type == 'exchange':
                    # self.log.debug("{b}", b=b)
                    if b_currency in coins:
                        # self.log.debug("{currency}", currency=b['currency'])
                        balances[b_currency] = float(b_available)  #balance that is available to trade

            if balances == {}:
                return None
            return balances

        d.addCallback(handleBody)
        d.addErrback(self.ratelimitErrhandler)

        return d

    def buy(self, pairs, price, amount):
        URL = "/v1/order/new"
        # self.log.debug("{url}", url=self.__url)
        url = self.__url + URL
        # self.log.debug("{url}", url=url)
        symbol = self.getSymbol(pairs)
        params = {
            'symbol': symbol,
            'amount': format(amount, '0.8f'),
            'price': str(price),
            'side': 'buy',
            'type': 'exchange limit',
            'exchange': 'bitfinex'
            }
        headers = getPostHeaders(url, URL, payload_params=params)
        d = post(reactor, url, headers=headers)

        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)
            # self.log.debug("{data}", data=data)

            assert 'order_id' in data, str(data)
            order_id = data['order_id']
            return int(order_id)
            # except KeyError:
            #     self.log.debug("{data}", data=data)
            #     order_id = '0'
            #     if 'error' in data:
            #         err = data['error']
            #         self.log.debug("{err}", err=err)
            #         if err == 'ERR_RATE_LIMIT':
            #             time.sleep(1)
            #     return (False, data)

        d.addCallback(handleBody)
        d.addErrback(self.defaultErrhandler)

        return d

    def sell(self, pairs, price, amount):
        URL = "/v1/order/new"
        # self.log.debug("{url}", url=self.__url)
        url = self.__url + URL
        # self.log.debug("{url}", url=url)
        symbol = self.getSymbol(pairs)
        params = {
            'symbol': symbol,
            'amount': format(amount, '0.8f'),
            'price': str(price),
            'side': 'sell',
            'type': 'exchange limit',
            'exchange': 'bitfinex'
            }
        headers = getPostHeaders(url, URL, payload_params=params)
        d = post(reactor, url, headers=headers)

        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)
            # self.log.debug("{data}", data=data)

            assert 'order_id' in data, str(data)
            order_id = data['order_id']
            return int(order_id)
            # try:
            #     order_id = data['order_id']
            #     return (True, int(order_id))
            # except KeyError:
            #     self.log.debug("{data}", data=data)
            #     order_id = '0'
            #     if 'error' in data:
            #         err = data['error']
            #         self.log.debug("{err}", err=err)
            #         if err == 'ERR_RATE_LIMIT':
            #             time.sleep(1)
            #     return (False, data)

        d.addCallback(handleBody)
        d.addErrback(self.defaultErrhandler)

        return d

    def getOrder(self, pairs, orderId):
        URL = "/v1/order/status"
        # self.log.debug("{url}", url=self.__url)
        url = self.__url + URL
        # self.log.debug("{url}", url=url)
        symbol = self.getSymbol(pairs)
        params = {}
        params['order_id'] = orderId
        headers = getPostHeaders(url, URL, payload_params=params)
        d = post(reactor, url, headers=headers)

        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)
            # self.log.debug("{data}", data=data)

            assert 'side' in data, str(data)
            side = data['side']
            price = float(data['price'])
            amount = float(data['original_amount'])
            is_cancelled = data['is_cancelled']
            is_live = data['is_live']
            timestamp = data['timestamp']
            # except KeyError:
            #     side = ''
            #     price = '0'
            #     amount = '0'
            #     is_cancelled = False
            #     is_live = False
            #     if 'error' in data:
            #         err = data['error']
            #         self.log.debug("{err}", err=err)
            #         if err == 'ERR_RATE_LIMIT':
            #             time.sleep(1)

            status = 'open'
            if 'error' in data:    #若有错误，status置为'error'
                status = 'error'
            elif is_cancelled:
                status = 'cancelled'
            elif not is_live:      #若没有被取消，并且不能继续被填充（not live），
                status = 'done'            #则表示交易已完成（done）
            order_data  = dict()
            order_data = {
                    'orderId': orderId,
                    'timestamp': timestamp,     #返回的字典中添加了时间戳信息
                    'type': side,
                    'iniPrice': price,
                    'initAmount': amount,
                    'coinPair': symbol,
                    'status': status
                    }
            return order_data

        d.addCallback(handleBody)
        d.addErrback(self.defaultErrhandler)

        return d

    def cancel(self, pairs, orderId):
        URL = "/v1/order/cancel"
        # self.log.debug("{url}", url=self.__url)
        url = self.__url + URL
        # self.log.debug("{url}", url=url)
        symbol = self.getSymbol(pairs)
        params = {}
        params['order_id'] = orderId
        headers = getPostHeaders(url, URL, payload_params=params)
        d = post(reactor, url, headers=headers)

        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)
            # self.log.debug("{data}", data=data)

            assert 'is_cancelled' in data, str(data)
            is_cancelled = data['is_cancelled']
            # except KeyError:
            #     is_cancelled = False
            #     if 'error' in data:
            #         err = data['error']
            #         self.log.debug("{err}", err=err)
            #         if err == 'ERR_RATE_LIMIT':
            #             time.sleep(1)
            #     return (False, data)
            if is_cancelled:
                return True
            else:
                return False

        d.addCallback(handleBody)
        d.addErrback(self.defaultErrhandler)

        return d

    def getOrderHistory(self, pairs, givenTime=float(time.time())-259200):
        #View your latest inactive orders. Limited to last 3 days and 1 request per minute.
        #All times are UTC timestamps expressed as seconds (eg 1477409622)
        #default givenTime:3 days ago
        URL = "/v1/orders/hist"
        # self.log.debug("{url}", url=self.__url)
        url = self.__url + URL
        # self.log.debug("{url}", url=url)
        symbol = self.getSymbol(pairs)
        headers = getPostHeaders(url, URL)
        d = post(reactor, url, headers=headers)

        def handleBody(body):
            # self.log.debug("{body}", body=body)
            data = json.loads(body)
            # self.log.debug("{data}", data=data)
            orderList = []

            assert isinstance(data, list), str(data)
            for order in data:
                assert 'price' in order, str(order)
                timestamp = order['timestamp']
                symbolGet = order['symbol'].upper()
                # self.log.debug("{symbolGet}{symbol}", symbolGet=symbolGet, symbol=symbol)
                if float(timestamp) >= givenTime and symbol==symbolGet:
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
                        'coinPair': order['symbol'],
                        'status': status
                        })
                # except KeyError:
                #     if 'error' in data:
                #         err = data['error']
                #         self.log.debug("{err}", err=err)
                #         if err == 'ERR_RATE_LIMIT':
                #             time.sleep(1)

            return orderList

        d.addCallback(handleBody)
        d.addErrback(self.ratelimitErrhandler)

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
                self.log.info("{data}", data=data)
                return None

        d.addCallback(handleBody)
        d.addErrback(self.defaultErrhandler)

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
                        self.log.error("{err}", err=err)
                        self.log.error("{kline}", kline=kline)
            return result
        d.addCallback(handleBody)
        d.addErrback(self.defaultErrhandler)

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
                self.log.error("{err}", err=err)
                return None
            return result
        d.addCallback(handleList)
        d.addErrback(self.defaultErrhandler)

        return d

bitfinex = Bitfinex(
    'https://api.bitfinex.com',
    ApiKey,
    SecretKey
    )
