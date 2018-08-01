from sys import argv
from pprint import pformat
from twisted.web.client import readBody
from twisted.web.client import BrowserLikePolicyForHTTPS
from twisted.web.http_headers import Headers
from agent import TunnelingAgent


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

def get(reactor, url):
    url = bytes(str(url), encoding="utf8")
    agent = TunnelingAgent(reactor, ('127.0.0.1', 1087, None), BrowserLikePolicyForHTTPS())
    d = agent.request(
        b'GET', url,
        Headers({'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36']}),
        None)
    d.addCallback(cbRequest)
    return d
