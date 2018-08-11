from twisted.internet import defer
from twisted.python.failure import Failure

import time


class Slot(object):
    def __init__(self, key):
        self.key = key
        self.data = None

    def setData(self, data=None):
        self.data = data

    def getData(self):
        return self.data

    def pop(self):
        result = self.getData()
        self.setData()
        return result


class Cycle(object):
    def __init__(self, reactor, f, key, limit=0):
        self.running = False
        self.fun = f
        self.limit = limit
        self.count = 0
        self.key = key
        self.slot = Slot(key)
        self.reactor = reactor

    @defer.inlineCallbacks
    def cbRun(self, *args, **kwargs):
        if self.running:
            data = None
            try:
                data = yield self.fun(*args, **kwargs)
            except Exception as err:
                failure = Failure(err)
                print(failure.getBriefTraceback())
            if data is None:
                self.slot.setData()
            else:
                self.slot.setData(data)
                print(self.getData())

            if self.limit > 0 :
                self.count += 1
                if self.count % self.limit == 0:
                    self.count = 0
                    # print('Wait for 1 second')
                    time.sleep(1)
                    # print('Continue')

            self.next(*args, **kwargs)

    def start(self, *args, **kwargs):
        if self.running:
            print('Cycle is running.')
        else:
            self.running = True
            self.reactor.callWhenRunning(self.cbRun, *args, **kwargs)

    def next(self, *args, **kwargs):
        self.reactor.callWhenRunning(self.cbRun, *args, **kwargs)

    def stop(self):
        self.running = False

    def getData(self):
        return self.slot.pop()
