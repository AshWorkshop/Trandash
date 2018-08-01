
from sys import argv
from pprint import pformat
import json
import time

from twisted.internet import task, defer
from twisted.internet import reactor
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers


def cbRequest(response):
    # print('Response version:', response.version)
    # print('Response code:', response.code)
    # print('Response phrase:', response.phrase)
    # print('Response headers:')
    # print(pformat(list(response.headers.getAllRawHeaders())))
    d = readBody(response)
    d.addCallback(cbBody)
    return d

def cbBody(body):
    # print('Response body:')
    return body

def getData(reactor, url=b"http://data.gateio.io/api2/1/orderBook/ETH_USDT"):
    agent = Agent(reactor)
    d = agent.request(
        b'GET', url,
        Headers({'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36']}),
        None)
    d.addCallback(cbRequest)
    return d

def cbCondition(body1, body2):
    ob1 = json.loads(body1)
    ob2 = json.loads(body2)
    print(ob1['asks'][0], ob2['bids'][0])

@defer.inlineCallbacks
def cbNext():
    print('looping')
    time.sleep(1)
    # d = task.deferLater(reactor, 0, main, reactor)
    try:
        body1 = yield getData(reactor, b"http://data.gateio.io/api2/1/orderBook/ETH_USDT")
        # body2 = yield getData(reactor, b"http://data.gateio.io/api2/1/orderBook/ETH_USDT")
        body2 = yield getData(reactor, b"https://api.bitfinex.com/v1/book/ETHUSD")
    except Exception as err:
        print(err)
    cbCondition(body1, body2)

    yield cbNext()



# loop = task.LoopingCall(cbLoop)
# loopDeferred = loop.start(1.0)
dfd = defer.Deferred()
reactor.callWhenRunning(cbNext)
reactor.run()
