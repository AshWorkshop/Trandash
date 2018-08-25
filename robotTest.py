from robots.base import RobotBase, CycleSource, Action, LoopSource
from twisted.internet import reactor, task
from exchanges.gateio.GateIOService import gateio
from exchanges.huobi.HuobiproService import huobipro

BIDS,ASKS = range(2)
PRICE,AMOUNT = range(2)

def counter():
    print('tick')

def books(newState,exchange):
    if newState[exchange]['orderbook'] is not None:
        if newState['orderbooks'] == {}:
            newState['orderbooks']['bids'] = newState[exchange]['orderbook'][BIDS]
            newState['orderbooks']['asks'] = newState[exchange]['orderbook'][ASKS]
        else:
            for order in newState['gateio']['orderbook'][BIDS]:
                level = 0
                while level < len(newState['orderbooks']['asks']):
                    if order[PRICE] == newState['orderbooks']['bids'][level][PRICE]:
                        newState['orderbooks']['bids'][level][AMOUNT] = (order[AMOUNT]+newState['orderbooks']['bids'][level][AMOUNT])/2
                        break
                    elif level == len(newState['orderbooks']['asks']):
                        newState['orderbooks']['bids'].append(order)
                    else:
                        level += 1



            for order in newState['gateio']['orderbook'][ASKS]:
                level = 0
                while level < len(newState['orderbooks']['asks']):
                    if order[PRICE] == newState['orderbooks']['asks'][level][PRICE]:
                        newState['orderbooks']['asks'][level][AMOUNT] = (order[AMOUNT]+newState['orderbooks']['asks'][level][AMOUNT])/2
                        break
                    elif level == len(newState['orderbooks']['asks']):
                        newState['orderbooks']['asks'].append(order)
                    else:
                        level += 1

    newState['orderbooks']['bids'].sort(reverse=True)
    newState['orderbooks']['asks'].sort()

    #level = 0
    #while level < len(newState['orderbooks']['bids']):
    #    level += 1
    #    if newState['orderbooks']['bids'][level-1] == newState['orderbooks']['bids'][level]:
    #        orderA = newState['orderbooks']['bids'].pop(level)
    #        newState['orderbooks']['bids'][level-1][AMOUNT] = (orderA[AMOUNT]+newState['orderbooks']['bids'][level-1][AMOUNT])/2

    if len(newState['orderbooks']['bids']) >= 50:
        newState['orderbooks']['asks'] = newState['orderbooks']['asks'][:50]
    if len(newState['orderbooks']['bids']) >= 50:
        newState['orderbooks']['bids'] = newState['orderbooks']['bids'][:50]

    return newState


class TestRobot(RobotBase):
    def launch(self, oldState, newState):
        actions = []
        print(newState.get('count'))
        if newState['count'] == 10 and newState.get('tickSource') is not None:
            print('STOP LISTEN TICKEVENT')
            self.stopListen(newState['tickSource'])
            # newState['tickSource'].stop()
        if newState['count'] == 15 and newState.get('tickSource') is None:
            print('START LISTEN TICKEVENT')
            self.listen(newState['tickBackup'])
        return actions

    def gateioOrderBookHandler(self, state, dataRecivedEvent):
        newState = dict()
        newState.update(state)
        newState['gateio'] = dict()
        newState['gateio'].update(state.get('gateio', dict()))
        newState['gateio']['orderbook'] = dataRecivedEvent.data['data']
        if newState['gateio']['orderbook'] is not None:
            for order in newState['gateio']['orderbook'][BIDS]:
                order.append('gateio')
            for order in newState['gateio']['orderbook'][ASKS]:
                order.append('gateio')

            newState['orderbooks'] = state.get('orderbooks',dict())
            #print(newState)
            newState = books(newState,'gateio')


        return newState

    def huobiproOrderBookHandler(self, state, dataRecivedEvent):
        newState = dict()
        newState.update(state)
        newState['huobipro'] = state.get('huobipro',dict())
        newState['huobipro']['orderBook'] = dataRecivedEvent.data['data']
        if newState['gateio']['orderbook'] is not None:
            for order in newState['huobipro']['orderbook'][BIDS]:
                order.append('huobipro')
            for order in newState['huobipro']['orderbook'][ASKS]:
                order.append('huobipro')

            newState['orderbooks'] = state.get('orderbooks',dict())
            #print(newState)
            newState = book(newState,'huobipro')

        return newState


    def tickHandler(self, state, tickEvent):
        newState = dict()
        newState.update(state)
        newState['count'] = state.get('count', 0) + 1

        return newState

    def systemEventHandler(self, state, systemEvent):
        newState = dict()
        newState.update(state)
        if systemEvent.data['type'] == 'LISTEN_STOPPED':
            if systemEvent.data['info']['source'] == state['tickSource']:
                newState['tickSource'] = None
                newState['tickBackup'] = systemEvent.data['info']['source']
        elif systemEvent.data['type'] == 'LISTEN_STARTED':
            if systemEvent.data['info']['source'] is not None and systemEvent.data['info']['source'] == state.get('tickBackup'):
                newState['tickSource'] = systemEvent.data['info']['source']
                newState['tickBackup'] = None

        return newState

gateioSource = CycleSource(reactor, gateio.getOrderBook, key='gateio', payload={
    'args': [('eth', 'usdt')]
})
huobiproSource = CycleSource(reactor,huobipro.getOrderBook, key='huobipro',payload={
    'args': [('eth','usdt')]
})

tickSource = LoopSource(
    reactor,
    counter
)

robot = TestRobot()
robot.listen([gateioSource,huobiproSource, tickSource])
robot.bind(
    'dataRecivedEvent',
    robot.gateioOrderBookHandler,
    'gateio'
)
robot.bind(
    'dataRecivedEvent',
    robot.huobiproOrderBookHandler,
    'huobipro'
)

robot.bind(
    'tickEvent',
    robot.tickHandler
)

robot.state.update({
    'tickSource': tickSource,
})

gateioSource.start()
#huobiproSource.start()
tickSource.start()
reactor.run()
