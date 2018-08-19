from twisted.internet import task

class Robot(object):

    def __init__(self, reactor, states=[], cycles=[]):
        self.reactor = reactor
        self.states = states
        self.state = None
        self.data = dict()
        self.data['cycleData'] = dict()
        self.count = 0
        self.waits = dict()
        self.cycles = cycles

        for state in states:
            assert hasattr(self, state)
            self.waits[state] = 0

    def cbRun(self):
        state = self.state
        self.count += 1
        print('[', self.count, state, ']')
        for cycle in self.cycles:
            self.data['cycleData'][cycle.key] = cycle.getData()

        for k, v in self.data['cycleData'].items():
            print(k, bool(v), sep=': ', end=' ')

        print('')

        if state:
            fun = getattr(self, state)
            fun()

    def ebFailed(self, failure):
        print(failure.getBriefTranceback())


    def start(self, state=None):
        # self.init(self.cycles)
        self.state = state
        self.loop = task.LoopingCall(self.cbRun)
        loopDeferred = self.loop.start(1.0)
        loopDeferred.addErrback(self.ebFailed)

        self.reactor.run()
