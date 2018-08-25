from robots.base import RobotBase, CycleSource, Action, LoopSource
from twisted.internet import reactor, task
from exchanges.gateio.GateIOService import gateio
from exchanges.huobi.HuobiproService import huobipro
from exchanges.sisty.SistyService import sisty
from exchanges.bitfinex.BitfinexService import bitfinex

import time

BIDS,ASKS = range(2)
PRICE,AMOUNT = range(2)

power = [0.5,0.5]

def counter():
    print('tick')

def books(newState,exchange):

    newState['orderbooks'] = dict()
    newState['orderbooks']['bids'] = newState[exchange[0]]['orderbook'][BIDS]
    newState['orderbooks']['asks'] = newState[exchange[0]]['orderbook'][ASKS]
    maxLevel = len(newState['orderbooks']['bids'])

    for order in newState[exchange[1]]['orderbook'][BIDS]:
        level = 0
        while level < maxLevel:
            if order[PRICE] == newState['orderbooks']['bids'][level][PRICE]:
                newState['orderbooks']['bids'][level][AMOUNT] = order[AMOUNT]*power[0]+newState['orderbooks']['bids'][level][AMOUNT]*power[1]
                break
            elif level == maxLevel:
                newState['orderbooks']['bids'].append(order)
            else:
                level += 1


    maxLevel = len(newState['orderbooks']['asks'])
    for order in newState[exchange[1]]['orderbook'][ASKS]:
        level = 0
        while level < maxLevel:
            if order[PRICE] == newState['orderbooks']['asks'][level][PRICE]:
                newState['orderbooks']['asks'][level][AMOUNT] = (order[AMOUNT]+newState['orderbooks']['asks'][level][AMOUNT])/2
                break
            elif level == maxLevel:
                newState['orderbooks']['asks'].append(order)
            else:
                level += 1

    newState['orderbooks']['bids'].sort(reverse=True)
    newState['orderbooks']['asks'].sort()
    newState['orderbooks']['time'] = time.time()
    return newState


class TestRobot(RobotBase):
    def launch(self, oldState, newState):
        actions = []
        if 'orderbooks' in newState:
            print(newState['orderbooks'])

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
            newState['gateio']['time'] = time.time()
            for order in newState['gateio']['orderbook'][BIDS]:
                order.append('gateio')
            for order in newState['gateio']['orderbook'][ASKS]:
                order.append('gateio')

            if 'huobipro' in newState:
                if time.time()-newState['huobipro']['time'] <= 300 and newState['huobipro']['orderbook'] is not None:
                    newState = books(newState,['gateio','huobipro'])

        return newState

    def huobiproOrderBookHandler(self, state, dataRecivedEvent):
        newState = dict()
        newState.update(state)
        newState['huobipro'] = state.get('huobipro',dict())
        newState['huobipro']['orderbook'] = dataRecivedEvent.data['data']
        if newState['huobipro']['orderbook'] is not None:
            newState['huobipro']['time'] = time.time()
            for order in newState['huobipro']['orderbook'][BIDS]:
                order.append('huobipro')
            for order in newState['huobipro']['orderbook'][ASKS]:
                order.append('huobipro')

            if 'gateio' in newState:
                if time.time()-newState['gateio']['time'] <= 300 and newState['gateio']['orderbook'] is not None:
                    newState = books(newState,['huobipro','gateio'])

        return newState

    def bitfinexOrderBookHandler(self, state, dataRecivedEvent):
        newState = dict()
        newState.update(state)
        newState['bitfinex'] = state.get('bitfinex',dict())
        newState['bitfinex']['orderbook'] = dataRecivedEvent.data['data']
        if newState['bitfinex']['orderbook'] is not None:
            newState['bitfinex']['time'] = time.time()
            for order in newState['bitfinex']['orderbook'][BIDS]:
                order.append('bitfinex')
            for order in newState['bitfinex']['orderbook'][ASKS]:
                order.append('bitfinex')

            newState['orderbooks'] = state.get('orderbooks',dict())
            #print(newState)
            newState = books(newState,'bitfinex')

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
bitfinexSource = CycleSource(reactor,bitfinex.getOrderBook, key='bitfinex',payload={
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
    'dataRecivedEvent',
    robot.bitfinexOrderBookHandler,
    'bitfinex'
)

robot.bind(
    'tickEvent',
    robot.tickHandler
)

robot.state.update({
    'tickSource': tickSource,
})

gateioSource.start()
huobiproSource.start()
tickSource.start()
reactor.run()
