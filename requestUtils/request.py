from pprint import pformat
import json

from twisted.web.client import readBody
from twisted.web.client import BrowserLikePolicyForHTTPS
from twisted.web.http_headers import Headers
from twisted.web.client import Agent, ProxyAgent, HTTPConnectionPool
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet import reactor
from requestUtils.agent import TunnelingAgent
from requestUtils.bytesprod import BytesProducer
import settings

from utils import to_bytes



def cbRequest(response):
    # print('Response version:', response.version)
    # print('Response code:', response.code)
    # print('Response phrase:', response.phrase)
    # print('Response headers:')
    # print(pformat(list(response.headers.getAllRawHeaders())))
    d = readBody(response)
    d.addCallback(cbBody)
    return d

def ebPrint(failure):
    print(failure)
    return failure

def cbBody(body):
    # print('Response body:')
    body = body.decode('utf8')
    return body

pool = HTTPConnectionPool(reactor)
endpoint = TCP4ClientEndpoint(reactor, settings.PROXY_ADDRESS, settings.PROXY_PORT)
tunnelingAgent = TunnelingAgent(reactor, (settings.PROXY_ADDRESS, settings.PROXY_PORT, None), BrowserLikePolicyForHTTPS(), pool=pool)
proxyAgent = ProxyAgent(endpoint, pool=pool)
normalAgent = Agent(reactor, pool=pool)
# pool = None

def get(reactor, url, headers={}, body=None):

    ssl = url.split(':')[0]

    if ssl == 'https' and settings.USE_PROXY:
        agent = tunnelingAgent
    else:
        if settings.USE_PROXY:
            agent = proxyAgent
        else:
            agent = normalAgent
    url = bytes(str(url), encoding="utf8")
    _body = None
    if body:
        _body = BytesProducer(to_bytes(body))
    d = agent.request(
        b'GET', url,
        Headers(headers),
        _body)
    d.addCallback(cbRequest)
    # d.addErrback(ebPrint)
    return d

def post(reactor, url, headers={}, body=None):

    ssl = url.split(':')[0]

    if ssl == 'https' and settings.USE_PROXY:
        agent = tunnelingAgent
    else:
        if settings.USE_PROXY:
            agent = proxyAgent
        else:
            agent = normalAgent
    url = bytes(str(url), encoding="utf8")
    _body = None
    if body:
        _body = BytesProducer(to_bytes(body))
    d = agent.request(
        b'POST', url,
        Headers(headers),
        _body)
    d.addCallback(cbRequest)
    # d.addErrback(ebPrint)
    return d
