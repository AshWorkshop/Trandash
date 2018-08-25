from robots.base import RobotBase, CycleSource, Action, LoopSource
from twisted.internet import reactor, task
from twisted.application import service
from exchanges.gateio.GateIOService import gateio
from exchanges.huobi.HuobiproService import huobipro
from exchanges.sisty.SistyService import sisty
from exchanges.bitfinex.BitfinexService import bitfinex

import time

BIDS,ASKS = range(2)
PRICE,AMOUNT = range(2)

POWER = [0.5,0.5]

def counter():
    print('tick')

def books(newState,exchange):

    newState['orderbooks'] = {'bids':[],'asks':[]}
    A,B = 0,0
    maxLevelA = len(newState[exchange[0]]['orderbook'][BIDS])
    maxLevelB = len(newState[exchange[1]]['orderbook'][BIDS])
    while A < maxLevelA and B < maxLevelB:
        orderA = newState[exchange[0]]['orderbook'][BIDS][A]
        orderB = newState[exchange[1]]['orderbook'][BIDS][B]
        if orderA[PRICE] == orderB[PRICE]:
            orderA[AMOUNT] = orderA[AMOUNT]*POWER[0] + orderB[AMOUNT]*POWER[1]
            newState['orderbooks']['bids'].append(orderA)
            A += 1
            B += 1
        elif orderA[PRICE] > orderB[PRICE]:
            newState['orderbooks']['bids'].append(orderA)
            A += 1
        else:
            newState['orderbooks']['bids'].append(orderB)
            B += 1
    if maxLevelA >= maxLevelB:
        while A < maxLevelA:
            orderA = newState[exchange[0]]['orderbook'][BIDS][A]
            newState['orderbooks']['bids'].append(orderA)
            A += 1
    elif maxLevelA < maxLevelB:
        while B < maxLevelB:
            orderB = newState[exchange[1]]['orderbook'][BIDS][B]
            newState['orderbooks']['bids'].append(orderB)
            B += 1

    A,B = 0,0
    maxLevelA = len(newState[exchange[0]]['orderbook'][ASKS])
    maxLevelB = len(newState[exchange[1]]['orderbook'][ASKS])
    while A < maxLevelA and B < maxLevelB:
        orderA = newState[exchange[0]]['orderbook'][ASKS][A]
        orderB = newState[exchange[1]]['orderbook'][ASKS][B]
        if orderA[PRICE] == orderB[PRICE]:
            orderA[AMOUNT] = orderA[AMOUNT]*POWER[0] + orderB[AMOUNT]*POWER[1]
            newState['orderbooks']['asks'].append(orderA)
            A += 1
            B += 1
        elif orderA[PRICE] < orderB[PRICE]:
            newState['orderbooks']['asks'].append(orderA)
            A += 1
        else:
            newState['orderbooks']['asks'].append(orderB)
            B += 1
    if maxLevelA >= maxLevelB:
        while A < maxLevelA:
            orderA = newState[exchange[0]]['orderbook'][BIDS][A]
            newState['orderbooks']['asks'].append(orderA)
            A += 1
    elif maxLevelA < maxLevelB:
        while B < maxLevelB:
            orderB = newState[exchange[1]]['orderbook'][BIDS][B]
            newState['orderbooks']['asks'].append(orderB)
            B += 1

    newState['orderbooks']['time'] = time.time()
    return newState

def cutOrderBook(orderBook, capacity=1):
    #orderBook: one of bids or asks (type: list)
    #return: cuttedOrderBook, also one of  bids or asks (list of: [price1, capacity],...,[priceN, remainAmount])
    cuttedOrderBook = list()

    for data in orderBook:
        remainAmount = data[AMOUNT]
        while remainAmount >= capacity:
            remainAmount -= capacity
            cuttedOrderBook.append([data[PRICE], capacity])
        if remainAmount != 0:
            cuttedOrderBook.append([data[PRICE], remainAmount])

    return cuttedOrderBook

def adjustOrderBook(oldState, newState, capacity=1):
    #思路1：将目标深度表按照capacity分割成小份的表，(用cutOrderBook()函数)
    #直接拿这份表和old表对比，
    #存在价格一样就不管，S中没有的价格就添加（挂单），S中有而目标深度小表中没有的价格就撤单
    #return: adjustmentDict ; eg:
    # { 'bids': [(276, 1), (276, 1), (274, 1), (274, 1), (274,1), ....], 
    #   'asks':[(278, 1), (278, 0.5), ...], 
    #   'cancle':[1357684 (# orderId), 1357898, ...]}
    adjustmentDict = dict()
    adjustmentDict['bids'] = list()
    adjustmentDict['asks'] = list()
    adjustmentDict['cancle'] = list()
    nBids = newState['orderbooks']['bids']
    cuttedBids = cutOrderBook(nBids)
    nAsks = newState['orderbooks']['asks']
    cuttedAsks = cutOrderBook(nAsks)
    for bid in oldState['sisty']['orderbook']['bids']:
        for cBid in cuttedBids:
            if bid[PRICE] == cBid[PRICE]:
                pass
            elif bid[PRICE] > cBid[PRICE]:
                orderId = 0 # TO DO: how to get orderId?
                adjustmentDict['cancle'].append(orderId)
            elif bid[PRICE] < cBid[PRICE]:
                adjustmentDict['bids'].append([cBid[PRICE], cBid[AMOUNT]])



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
                if (time.time()-newState['huobipro']['time']) <= 300 and newState['huobipro']['orderbook'] is not None:
                    newState = books(newState,['gateio','huobipro'])

        return newState

    def huobiproOrderBookHandler(self, state, dataRecivedEvent):
        newState = dict()
        newState.update(state)
        newState['huobipro'] = dict()
        newState['huobipro'] = state.get('huobipro',dict())
        newState['huobipro']['orderbook'] = dataRecivedEvent.data['data']
        if newState['huobipro']['orderbook'] is not None:
            newState['huobipro']['time'] = time.time()
            for order in newState['huobipro']['orderbook'][BIDS]:
                order.append('huobipro')
            for order in newState['huobipro']['orderbook'][ASKS]:
                order.append('huobipro')

            if 'gateio' in newState:
                if (time.time()-newState['gateio']['time']) <= 300 and newState['gateio']['orderbook'] is not None:
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

class RobotService(service.Service):
    
    def startService(self):
        print('starting robot service...')
        robot.listen([gateioSource, huobiproSource, tickSource])
        gateioSource.start()
        huobiproSource.start()
        tickSource.start()
    
    def stopService(self):
        print('stopping robot service...')
        gateioSource.stop()
        huobiproSource.stop()
        tickSource.stop()
