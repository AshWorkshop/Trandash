from exchanges.base import ExchangeService
from request import get
from .huobipro_key import AccessKey, SecretKey
import requests
import datetime
import hashlib
import hmac
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
        params.update({'AccessKeyId': AccessKey,
                       'SignatureMethod': 'HmacSHA256',
                       'SignatureVersion': '2',
                       'Timestamp': timestamp})

        host_url = self.__trade_url
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        params['Signature'] = self.createSign(params, method, host_name, request_path, self.__secretKey)

        url = host_url + request_path
        return (url, params)

    def api_key_post(self,params, request_path):
        method = 'POST'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params_to_sign = {'AccessKeyId': AccessKey,
                          'SignatureMethod': 'HmacSHA256',
                          'SignatureVersion': '2',
                          'Timestamp': timestamp}

        host_url = self.__trade_url
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        params_to_sign['Signature'] = createSign(params_to_sign, method, host_name, request_path, self.__secretKey)
        url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
        return http_post_request(url, params)

    def getOrderBook(self, pairs,grade=0):
        URL = "/market/depth?"

        params={'symbol':self.getSymbol(pairs),
                'type':self.toGradeStr(grade),
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
            bids = data['tick']['bids']
            asks = data['tick']['asks']
            return [bids, asks]

        d.addCallback(handleBody)
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
            "Accept": "application/json",
            'Content-Type': 'application/json'
        }
        postdata = urllib.parse.urlencode(params)
        response = requests.get(url, postdata, headers=headers, timeout=5)
        print(response.json())

        return response.json()

    def getBalance(self, coin):

        accounts = self.get_accounts()
        acct_id = accounts['data'][0]['id'];

        url = "/v1/account/accounts/{0}/balance".format(acct_id)
        params = {"account-id": acct_id}
        url,params = self.api_key_get(params, url)
        headers = {
            "Content-type": ["application/x-www-form-urlencoded"],
            'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'],
        }
        postdata = urllib.parse.urlencode(params)
        url = url +'?'+ postdata

        d = get(reactor,url,headers = headers)

        def handleBody(body):
            data = json.loads(body)
            print(data['data']['list'])
            for b in data['data']['list']:
                if b['currency'] == 'hb10':
                    balance = b['balance']
                else:
                    balance = None
            return balance

        d.addCallback(handleBody)

        return d

    def buy(self, coinPair, price, amount):
        pass


huobi = Huobipro({'MARKET_URL':"https://api.huobi.pro",
                'TRADE_URL':"https://api.huobi.pro"},
                AccessKey,
                SecretKey)
