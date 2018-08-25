from robots.base import RobotBase, CycleSource, Action, LoopSource
from twisted.internet import reactor, task
from exchanges.gateio.GateIOService import gateio

def counter():
    print('tick')

class TestRobot(RobotBase):
    def launch(self, oldState, newState):
        actions = []
        print(newState)
        # if newState['gateio']['orderbook'] is not None:
        #     action = Action(reactor, gateio.buy, payload={
        #         'args': [('eth', 'usdt'), 2, 1]
        #     })
        #     actions.append(action)
        return actions

    def gateioOrderBookHandler(self, state, dataRecivedEvent):
        newState = dict()
        newState.update(state)
        newState['gateio'] = state.get('gateio', dict())
        newState['gateio']['orderbook'] = dataRecivedEvent.data['data']

        return newState

    def tickHandler(self, state, tickEvent):
        newState = dict()
        newState.update(state)
        newState['count'] = state.get('count', 0) + 1

        return newState

gateioSource = CycleSource(reactor, gateio.getOrderBook, key='gateio', payload={
    'args': [('eth', 'usdt')]
})

tickSource = LoopSource(
    reactor,
    counter
)

robot = TestRobot()
robot.listen([gateioSource, tickSource])
robot.bind(
    'dataRecivedEvent',
    robot.gateioOrderBookHandler,
    'gateio'
)
robot.bind(
    'tickEvent',
    robot.tickHandler
)
gateioSource.start()
tickSource.start()
reactor.run()