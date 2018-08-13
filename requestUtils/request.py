from pprint import pformat
import json

from twisted.web.client import readBody
from twisted.web.client import BrowserLikePolicyForHTTPS
from twisted.web.http_headers import Headers
from twisted.web.client import Agent
from requestUtils.agent import TunnelingAgent
from requestUtils.bytesprod import BytesProducer
from settings import USE_PROXY

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

def cbBody(body):
    # print('Response body:')
    body = body.decode('utf8')
    return body

def get(reactor, url, headers={}, body=None):

    ssl = url.split(':')[0]

    if ssl == 'https' and  USE_PROXY:
        agent = TunnelingAgent(reactor, ('127.0.0.1', 1087, None), BrowserLikePolicyForHTTPS())
    else:
        agent = Agent(reactor)
    url = bytes(str(url), encoding="utf8")
    _body = None
    if body:
        _body = BytesProducer(to_bytes(body))
    d = agent.request(
        b'GET', url,
        Headers(headers),
        _body)
    d.addCallback(cbRequest)
    return d

def post(reactor, url, headers={}, body=None):

    ssl = url.split(':')[0]

    if ssl == 'https' and USE_PROXY:
        agent = TunnelingAgent(reactor, ('127.0.0.1', 1087, None), BrowserLikePolicyForHTTPS())
    else:
        agent = Agent(reactor)
    url = bytes(str(url), encoding="utf8")
    _body = None
    if body:
        _body = BytesProducer(to_bytes(body))
    d = agent.request(
        b'POST', url,
        Headers(headers),
        _body)
    d.addCallback(cbRequest)
    return d
