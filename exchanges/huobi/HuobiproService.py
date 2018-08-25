from exchanges.base import ExchangeService
from requestUtils.request import get,post
from .huobipro_key import AccessKey, SecretKey
from utils import Order
import requests
import datetime
import hashlib
import hmac
import time
import base64

from twisted.internet import reactor

import json
import urllib.parse

class Huobipro(ExchangeService):

    def __init__(self, url, accessKey, secretKey):
        self.__market_url = url['MARKET_URL']
        self.__trade_url = url['TRADE_URL']
        self.__accessKey = accessKey
        self.__secretKey = secretKey
        self.__acct_id = self.get_accounts()
    def getHeaders(self):
        return {
            "Content-type": ["application/x-www-form-urlencoded"],
            'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'],
        }

    def postHeaders(self):
        return {
            "Accept": ["application/json"],
            'Content-Type': ['application/json']
        }

    def getAcctId(self):
        return self.__acct_id

    def getSymbol(self, pairs):
        return ''.join(pairs)

    def toGradeStr(self,grade):
        return ('step'+str(grade))

    def createSign(self,pParams, method, host_url, request_path, secret_key):
        sorted_params = sorted(pParams.items(), key=lambda d: d[0], reverse=False)
        encode_params = urllib.parse.urlencode(sorted_params)
        payload = [method, host_url, request_path, encode_params]
        payload = '\n'.join(payload)
        payload = payload.encode(encoding='UTF8')
        secret_key = secret_key.encode(encoding='UTF8')

        digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        signature = signature.decode()
        return signature

    def api_key_get(self,params, request_path):
        method = 'GET'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params.update({'AccessKeyId': self.__accessKey,
                       'SignatureMethod': 'HmacSHA256',
                       'SignatureVersion': '2',
                       'Timestamp': timestamp})

        host_url = self.__trade_url
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        params['Signature'] = self.createSign(params, method, host_name, request_path, self.__secretKey)

        url = host_url + request_path
        return url, params

    def api_key_post(self,params, request_path):
        method = 'POST'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params_to_sign = {'AccessKeyId': self.__accessKey,
                          'SignatureMethod': 'HmacSHA256',
                          'SignatureVersion': '2',
                          'Timestamp': timestamp}

        host_url = self.__trade_url
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        params_to_sign['Signature'] = self.createSign(params_to_sign, method, host_name, request_path, self.__secretKey)
        url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
        return url, params

    def getOrderBook(self, pairs,grade=0):
        URL = "/market/depth?"

        params={'symbol':self.getSymbol(pairs),
                'type':'percent10'
        }
        postdata = urllib.parse.urlencode(params)
        url = self.__market_url + URL + postdata

        headers = {
            "Content-type": ["application/x-www-form-urlencoded"],
            'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'],
        }
        d = get(reactor,url,headers = headers)

        def handleBody(body):
            #print(body)
            data = json.loads(body)
            #print(data)
            bids = data['tick']['bids'] #买单
            asks = data['tick']['asks'] #卖单
            return [bids, asks]

        d.addCallback(handleBody)
        d.addErrback(handleBody)
        #print(b)
        return d

    def get_accounts(self):
        """
        :return:
        """

        path = "/v1/account/accounts"
        params = {}
        url,params = self.api_key_get(params, path)
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
        }
        postdata = urllib.parse.urlencode(params)
        response = requests.get(url,postdata, headers=headers,timeout=5)
        data = response.json()
        try:
            if response.status_code == 200 and data['status'] == 'ok':
                return data['data'][0]['id']
        except :
            print("No acct_id")
            return

    def getBalance(self, coin):

        #accounts = self.get_accounts()
        #print(accounts)
        acct_id = self.getAcctId()

        url = "/v1/account/accounts/{0}/balance".format(acct_id)
        params = {"account-id": acct_id}
        url,params = self.api_key_get(params, url)
        headers = self.postHeaders()
        postdata = urllib.parse.urlencode(params)
        url = url +'?'+ postdata

        d = get(reactor,url,headers = headers)

        def handleBody(body):
            data = json.loads(body)
            for b in data['data']['list']:
                if b['currency'] == coin and b['type'] == 'trade':
                    balance = b['balance']
                    break
                else:
                    balance = 0.0

            return balance

        d.addCallback(handleBody)

        return d

    def getBalances(self, coins=[]):

        #accounts = self.get_accounts()
        #print(accounts)
        acct_id = self.getAcctId()

        url = "/v1/account/accounts/{0}/balance".format(acct_id)
        params = {"account-id": acct_id}
        url,params = self.api_key_get(params, url)
        headers = self.postHeaders()
        postdata = urllib.parse.urlencode(params)
        url = url +'?'+ postdata

        d = get(reactor,url,headers = headers)

        def handleBody(body):
            data = json.loads(body)
            balances = dict()
            if not isinstance(data, dict):
                return None
            for b in data['data']['list']:
                try:
                    b_type = b['type']
                    b_currency = b['currency']
                    b_available = b['balance']
                except KeyError:
                    b_type = ''
                    b_currency = ''
                    b_available = 0.0
                    if 'error' in data:
                        err = data['error']
                        print(err)
                if b_type == 'trade':
                    if b_currency in coins:
                        balances[b_currency] = float(b_available)

            return balances

        d.addCallback(handleBody)

        return d

    def buy(self, coinPair, price, amount):

#    {amount: "0.001", price: "466.10", type: "sell-limit", source: "web", symbol: "ethusdt",…}
        params = {"account-id": self.getAcctId(),
                  "amount": amount,
                  "symbol": self.getSymbol(coinPair),
                  "type": "buy-limit",
                  "source": "web",
                  "price":price
                  }
        url = '/v1/order/orders/place'
        url,params = self.api_key_post(params,url)
        headers = self.postHeaders()
        postdata = json.dumps(params)
        d = post(reactor,url, headers=headers, body = postdata)

        def handleBody(body):
            data = json.loads(body)
            print(data)
            try:
                order_id = data['data']
                return (True,int(order_id))
            except KeyError:
                print(data)
                order_id = '0'
                if 'err-msg' in data:
                    err = data['err-msg']
                    print(err)
                    return (False, data['err-msg'])

        d.addCallback(handleBody)

        return d

    def sell(self, coinPair, price, amount):

        params = {"account-id": self.getAcctId(),
                  "amount": amount,
                  "symbol": self.getSymbol(coinPair),
                  "type": "sell-limit",
                  "source": "web",
                  "price":price
                  }
        url = '/v1/order/orders/place'
        url,params = self.api_key_post(params,url)
        headers = self.postHeaders()
        postdata = json.dumps(params)
        d = post(reactor,url,headers=headers,body=postdata)

        def handleBody(body):
            data = json.loads(body)
            print(data)
            try:
                order_id = data['data']
                return (True,int(order_id))
            except KeyError:
                print(data)
                order_id = '0'
                if 'err-msg' in data:
                    err = data['err-msg']
                    print(err)
                    return (False, data['err-msg'])


        d.addCallback(handleBody)

        return d

    def getOrder(self, orderId, coinPair=None):
        params = {}
        url = "/v1/order/orders/{0}".format(orderId)
        url,params = self.api_key_get(params,url)
        headers = self.getHeaders()
        postdata = urllib.parse.urlencode(params)
        url = url + '?' +postdata
        d = get(reactor,url,headers=headers)

        def handleBody(body):
            data = json.loads(body)
            if data['data']['type']=='buy-limit':
                data['data']['type']='buy'
            elif data['data']['type']=='sell-limit':
                data['data']['type']='sell'

            #print(data)

            order = {
                "orderId":orderId,
                "type":data['data']['type'],
                "initPrice":float(data['data']['price']),
                "initAmount":float(data['data']['amount']),
                "coinPair":data['data']['symbol'],
                "status": data['states']
            }

            return (True, order)

        d.addCallback(handleBody)

        return d

    def cancelOrder(self, orderId, coinPair=None):
        params = {}
        url = "/v1/order/orders/{0}/submitcancel".format(orderId)
        url,params = self.api_key_post(params,url)
        headers = self.postHeaders()
        postdata = json.dumps(params)
        d = post(reactor,url,headers=headers,body=postdata)

        def handleBody(body):
            data = json.loads(body)
            if data['status'] == 'ok':
                return (True,data)
            elif data['status'] == 'error':
                return (False,data['err-code'],data['err-msg'])

        d.addCallback(handleBody)

        return d

    def getOrderHistory(self, pairs, start_date=None,end_date=float(time.time())):
        """

        :param symbol:
        :param states: 可选值 {pre-submitted 准备提交, submitted 已提交, partial-filled 部分成交, partial-canceled 部分成交撤销, filled 完全成交, canceled 已撤销}
        :param types: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param start_date:
        :param end_date:
        :param _from:
        :param direct: 可选值{prev 向前，next 向后}
        :param size:
        :return:
        """
        _from = None
        types = None
        states = 'submitted,partial-filled,partial-canceled,filled,canceled'
        size = None
        direct = "prev"
        symbol = self.getSymbol(pairs)
        params = {'symbol': symbol,
                  'states': states}

        if types:
            params['types'] = types
        if start_date:
            params['start-date'] = start_date
        if end_date:
            params['end-date'] = end_date
        if _from:
            params['from'] = _from
        if direct:
            params['direct'] = direct
        if size:
            params['size'] = size
        url = '/v1/order/orders'
        url,params = self.api_key_get(params, url)
        headers = self.getHeaders()
        postdata = urllib.parse.urlencode(params)
        url = url + '?' +postdata
        d = get(reactor,url,headers=headers)

        def handleBody(body):
            # print(body)
            data = json.loads(body)
            # print(data)
            orderList = []

            if not isinstance(data, dict):
                return None

            for order in data['data']:
                try:
                    if order['type'] == 'sell-limit':
                        order['type'] = 'sell'
                    elif order['type'] == 'buy-limit':
                        order['type'] = 'buy'

                    if order['state'] == 'filled':
                        order['state'] = 'done'
                    elif order['state'] == 'canceled':
                        order['state'] = 'cancelled'
                    orderList.append({
                        'orderId': order['id'],
                        'timestamp': order['finished-at'],    #返回的字典中添加了时间戳信息
                        'type': order['type'],
                        'iniPrice': float(order['price']),
                        'initAmount': float(order['amount']),
                        'coinPair': symbol,
                        'status': order['state']
                        })
                except KeyError:
                    if 'error' in data:
                        err = data['error']
                        print(err)

            return orderList

        d.addCallback(handleBody)

        return d
#1533793328920
#1533870669146 2018:11:11


huobipro = Huobipro({'MARKET_URL':"https://api.huobi.pro",
                'TRADE_URL':"https://api.huobi.pro"},
                AccessKey,
                SecretKey)
