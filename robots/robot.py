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

        for state in stateList:
            assert hasattr(self, state)
            self.waits[state] = 0

    def cbRun(self):
        state = self.state
        for cycle in self.cycles:
            self.data['cycleData'][cycle.key] = cycle.getData()

        for k, v in self.data['cycleData'].items():
            print(k, bool(v), sep=': ', end=' ')

        print('')

        count += 1
        print('[', count, state, ']')

        if status:
            fun = getattr(self, state)
            fun()
