from sys import argv
from pprint import pformat
import json
from twisted.web.client import readBody
from twisted.web.client import BrowserLikePolicyForHTTPS
from twisted.web.http_headers import Headers
from agent import TunnelingAgent
from bytesprod import BytesProducer


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

def get(reactor, url, headers={}, body=None):
    url = bytes(str(url), encoding="utf8")
    agent = TunnelingAgent(reactor, ('127.0.0.1', 1087, None), BrowserLikePolicyForHTTPS())
    _body = None
    if body:
        _body = BytesProducer(body)
    d = agent.request(
        b'GET', url,
        Headers(headers),
        _body)
    d.addCallback(cbRequest)
    return d

def post(reactor, url, headers={}, body=None):
    url = bytes(str(url), encoding="utf8")
    agent = TunnelingAgent(reactor, ('127.0.0.1', 1087, None), BrowserLikePolicyForHTTPS())
    _body = None
    if body:
        _body = BytesProducer(body)
    d = agent.request(
        b'POST', url,
        Headers(headers),
        _body)
    d.addCallback(cbRequest)
    return d
