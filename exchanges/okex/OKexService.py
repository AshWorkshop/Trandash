from utils import Order
from exchanges.base import ExchangeService
from requestUtils.request import get, post
from exchanges.okex.okex_key import ApiKey, SecretKey

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

    def ebFailed(self, failure):
        print(failure)
        return None

    def getTicker(self, pairs, contractType='quarter'):
        URL = "/api/v1/future_ticker.do"

        params = {
            'symbol': self.getSymbol(pairs),
            'contract_type': contractType
        }

        def handleBody(body):
            data = json.loads(body)
            assert 'ticker' in data
            return data['ticker']

        return httpGet(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

    def getKLine(self, pairs, contractType='quarter', ktype='1min', size=0, since=0):
        URL = "/api/v1/future_kline"

        params = {
            'symbol': self.getSymbol(pairs),
            'contract_type': contractType,
            'type': ktype,
            'size': str(size),
            'since': str(since)
        }

        def handleBody(body):
            data = json.loads(body)
            return data

        return httpGet(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

    def getKLineLastMin(self, pairs, contractType='quarter', last=0):
        t = int(round(time.time() * 1000))
        sincet = t - last * 60 * 1100
        d = self.getKLine(pairs, contractType=contractType, since=sincet)

        def handleList(KLines):
            result = []
            assert len(KLines) >= last
            result = KLines[-last:]
            return result

        d.addCallback(handleList)
        d.addErrback(self.ebFailed)

        return d


    def getHoldAmount(self, pairs, contractType='quarter'):
        URL = "/api/v1/future_hold_amount"

        params = {
            'symbol': self.getSymbol(pairs),
            'contract_type': contractType
        }

        def handleBody(body):
            data = json.loads(body)
            assert len(data) > 0
            assert 'amount' in data[0]
            return data[0]['amount']

        return httpGet(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

    def getOrderBook(self, pairs):
        URL = "/api/v1/future_depth.do"
        # print(self.__url)

        params = {
            'symbol': self.getSymbol(pairs),
            'contract_type': 'quarter',
        }

        def handleBody(body):
            data = json.loads(body)
            assert 'bids' in data and 'asks' in data
            bids = data['bids']
            asks = data['asks']
            asks.reverse()
            return [bids, asks]

        return httpGet(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

    def getPosition(self, pairs):
        URL = "/api/v1/future_position"

        params = {
            'symbol': self.getSymbol(pairs),
            'contract_type': 'quarter',
            'api_key': self.__accessKey,
        }
        sign = buildMySign(params, self.__secretKey)
        params['sign'] = sign

        def handleBody(body):
            data = json.loads(body)
            assert 'holding' in data and len(data['holding']) > 0
            return data['holding'][0]


        return httpPost(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

    def trade(self, pairs, contractType="quarter", price="", amount="", tradeType="", matchPrice="", leverRate=""):
        """
        参数名	参数类型	必填	描述
        api_key	String	是	用户申请的apiKey
        symbol	String	是	btc_usd ltc_usd eth_usd etc_usd bch_usd
        contract_type	String	是	合约类型: this_week:当周 next_week:下周 quarter:季度
        orders_data	String	是	JSON类型的字符串 例：[{price:5,amount:2,type:1,match_price:1},{price:2,amount:3,type:1,match_price:1}] 最大下单量为5，price,amount,type,match_price参数参考future_trade接口中的说明
        sign	String	是	请求参数的签名
        lever_rate	String	否	杠杆倍数，下单时无需传送，系统取用户在页面上设置的杠杆倍数。且“开仓”若有10倍多单，就不能再下20倍多单
        """
        URL = "/api/v1/future_trade.do"
        params = {
            'api_key': self.__accessKey,
            'symbol': self.getSymbol(pairs),
            'contract_type': contractType,
            'amount': amount,
            'type': tradeType,
            'match_price': matchPrice,
        }

        if price:
            params['price'] = price

        if leverRate:
            params['lever_rate'] = leverRate


        sign = buildMySign(params, self.__secretKey)
        params['sign'] = sign

        def handleBody(body):
            data = json.loads(body)
            assert 'result' in data
            if data['result'] == False:
                print(data)
                return None
            else:
                assert 'order_id' in data
                return data['order_id']

        return httpPost(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

    def cancle(self, pairs, contractType="quarter", orderId=""):
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
            assert 'result' in data
            if data['result']:
                return (True, orderId)
            else:
                print(data)
                return (False, data.get('error_code', -1))

        return httpPost(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

    def getOrder(self, pairs, contractType='quarter', orderId="", status=""):
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
            return data.get('orders', None)

        return httpPost(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)


    def getUserInfo(self, coin):
        URL = "/api/v1/future_userinfo"
        params = {
            "api_key": self.__accessKey,
        }
        sign = buildMySign(params, self.__secretKey)
        params['sign'] = sign

        def handleBody(body):
            data = json.loads(body)
            # print(data)
            if data.get('result', False):
                return data.get('info', {}).get(coin)
            else:
                return None

        return httpPost(self.__url, URL, params, callback=handleBody, errback=self.ebFailed)

okexFuture = OKexFuture(
    'https://www.okex.com',
    ApiKey,
    SecretKey
)
