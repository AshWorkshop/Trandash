from twisted.internet import defer
from twisted.python.failure import Failure

from exchanges.okex.OKexService import okexFuture

EXCHANGE = {
    'okexFuture': okexFuture
}

class Slot(object):
    def __init__(self, key):
        self.key = key
        self.data = dict()
    
    def setData(self, data=dict()):
        self.data = data

    def getData(self):
        return self.data.copy()

    def pop(self):
        result = self.getData()
        self.setData()
        return result


class KLineCycle(object):
    def __init__(self, key):
        self.running = False
        self.key = key
        self.slot = Slot(key)

    @defer.inlineCallbacks
    def cbRun(self, *args, **kwargs):
        if self.running:
            klines = []
            try:
                klines = yield EXCHANGE[self.key].getKLineLastMin(*args, **kwargs)
            except Exception as err:
                failure = Failure(err)
                print(failure.getBriefTraceback())
            if klines == []:
                self.slot.setData()
            else:
                self.slot.setData({'klines': klines})

            yield self.cbRun(*args, **kwargs)

    def start(self, reactor, *args, **kwargs):
        if self.running:
            print('Cycle is running.')
        else:
            self.running = True
            reactor.callWhenRunning(self.cbRun, *args, **kwargs)

    def stop(self):
        self.running = False

    def getData(self):
        return self.slot.pop()

class TickerCycle(object):
    def __init__(self, key):
        self.running = False
        self.key = key
        self.slot = Slot(key)

    @defer.inlineCallbacks
    def cbRun(self, *args, **kwargs):
        if self.running:
            ticker = {}
            try:
                ticker = yield EXCHANGE[self.key].getTicker(*args, **kwargs)
            except Exception as err:
                failure = Failure(err)
                print(failure.getBriefTraceback())
            if ticker == {}:
                self.slot.setData()
            else:
                self.slot.setData({'ticker': ticker})

            yield self.cbRun(*args, **kwargs)

    def start(self, reactor, *args, **kwargs):
        if self.running:
            print('Cycle is running.')
        else:
            self.running = True
            reactor.callWhenRunning(self.cbRun, *args, **kwargs)

    def stop(self):
        self.running = False

    def getData(self):
        return self.slot.pop()


class PositionCycle(object):
    def __init__(self, key):
        self.running = False
        self.key = key
        self.slot = Slot(key)

    @defer.inlineCallbacks
    def cbRun(self, *args, **kwargs):
        if self.running:
            data = {}
            try:
                data = yield EXCHANGE[self.key].getPosition(*args, **kwargs)
            except Exception as err:
                failure = Failure(err)
                print(failure.getBriefTraceback())
            if data == {}:
                self.slot.setData()
            else:
                self.slot.setData({'position': data})

            yield self.cbRun(*args, **kwargs)

    def start(self, reactor, *args, **kwargs):
        if self.running:
            print('Cycle is running.')
        else:
            self.running = True
            reactor.callWhenRunning(self.cbRun, *args, **kwargs)

    def stop(self):
        self.running = False

    def getData(self):
        return self.slot.pop()


class OrderBookCycle(object):
    def __init__(self, key):
        self.running = False
        self.key = key
        self.slot = Slot(key)

    @defer.inlineCallbacks
    def cbRun(self, *args, **kwargs):
        if self.running:
            orderBook = {}
            try:
                orderBook = yield EXCHANGE[self.key].getOrderBook(*args, **kwargs)
            except Exception as err:
                failure = Failure(err)
                print(failure.getBriefTraceback())
            if orderBook == {}:
                self.slot.setData()
            else:
                self.slot.setData({'orderBook': orderBook})

            yield self.cbRun(*args, **kwargs)

    def start(self, reactor, *args, **kwargs):
        if self.running:
            print('Cycle is running.')
        else:
            self.running = True
            reactor.callWhenRunning(self.cbRun, *args, **kwargs)

    def stop(self):
        self.running = False

    def getData(self):
        return self.slot.pop()