from robots.base import RobotBase, CycleSource, Action, LoopSource
from twisted.internet import reactor, task
from twisted.application import service
from exchanges.gateio.GateIOService import gateio
from exchanges.huobi.HuobiproService import huobipro
from exchanges.sisty.SistyService import sisty
from exchanges.bitfinex.BitfinexService import bitfinex
from utils import adjustOrderBook,commitOrderBook

import time

TIME = 0.0

BIDS,ASKS = range(2)
PRICE,AMOUNT,EXCHANGE = range(3)
ORDERID = 2

POWER = [0.5,0.5]
coinPairs = ('eth','usdt')

EXCHANGES = {
    "huobipro":huobipro,
    "gateio":gateio,
    "bitfinex":bitfinex,
    "sisty":sisty
}

def counter():
    print('tick')

class TestRobot(RobotBase):
    def launch(self, oldState, newState):
        global TIME
        actions = []
        #print(newState)

        #订单管理
        if 'sisty' in newState and 'sisty' in oldState:

            old = oldState['sisty']['orders']['content']
            new = newState['sisty']['orders']['content']

            oldOrders = old['datas']
            newOrders = new['datas']

            for orderA in oldOrders:
                if orderA['createtime'] < TIME:
                    break
                for orderB in newOrders:
                    if orderB['createtime'] < TIME:
                        break
                    print(orderB)
                    print(orderA)
                    staFile = open('sistyTest,orderManaged')
                    staFile.write("orderA:%d ,\n orderB:%d" % (orderA,orderB))
                    staFile.close()
                    exchange = None
                    type = None
                    price = None
                    amount = None
                    if orderA['id'] == orderB['id']:
                        amount = abs(orderA['surplusamount']-orderB['surplusamount'])
                        if orderA['type'] == 1:
                            type = "buy"
                        elif orderA['type'] == 2:
                            type = "sell"
                        if "orderbooks" in newState:
                            if type == "buy":
                                book = "bids"
                            elif type == "sell":
                                book = "asks"
                            for orderC in newState['orderbooks'][book]:
                                if orderC[PRICE] == orderA['entrustprice']:
                                    price = orderC[PRICE]
                                    exchange = orderC[EXCHANGE]

                    if exchange is not None and type is not None and price is not None and amount is not None:
                        if type == "buy":
                            action = Action(reactor,EXCHANGES[exchange].sell,key=exchange+"sell",payload={
                                "args":[coinPairs,price,amount]
                            })
                        if type == "sell":
                            action = Action(reactor,EXCHANGES[exchange].buy,key=exchange+"buy",payload={
                                "args":[coinPairs,price,amount]
                            })
                        actions.append(action)
        #调整深度
        if 'orderbooks' in newState and 'sisty' in newState :
            adjustmentDict = adjustOrderBook(newState)
            exchange = 'sisty'
            if adjustmentDict['bids'] is not None:
                for bid in adjustmentDict['bids']:
                    price = bid[PRICE]
                    amount = bid[AMOUNT]
                    action = Action(reactor,EXCHANGES[exchange].trade,key=exchange+"buy",wait=True,payload={
                                        "args":[coinPairs,price,amount,1]
                                    })
                    actions.append(action)

            if adjustmentDict['asks'] is not None:
                for ask in adjustmentDict['asks']:
                    price = ask[PRICE]
                    amount = ask[AMOUNT]
                    action = Action(reactor,EXCHANGES[exchange].trade,key=exchange+"sell",wait=True,payload={
                                        "args":[coinPairs,price,amount,2]
                                    })
                    actions.append(action)

            if adjustmentDict['cancle'] is not None:
                for cancleId in adjustmentDict['cancle']:
                    action = Action(reactor,EXCHANGES[exchange].cancle,key=exchange+"cancle",wait=True,payload={
                                        "args":[coinPairs,cancleId]
                                    })
                    actions.append(action)

        #print(newState['data']['content']['datas'])

        print(newState.get('count'))
        # if newState['count'] == 10 and newState.get('tickSource') is not None:
        #     print('STOP LISTEN TICKEVENT')
        #     self.stopListen(newState['tickSource'])
        #     # newState['tickSource'].stop()
        # if newState['count'] == 15 and newState.get('tickSource') is None:
        #     print('START LISTEN TICKEVENT')
        #     self.listen(newState['tickBackup'])
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
                    newState = commitOrderBook(newState,['gateio','huobipro'])

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
                    newState = commitOrderBook(newState,['huobipro','gateio'])

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
            newState = commitOrderBook(newState,'bitfinex')

        return newState

    def sistyOrderHandler(self,state,dataRecivedEvent):
        newState = dict()
        newState.update(state)
        newState['ststy'] = dict()
        newState['sisty'] = state.get('sisty',dict())
        newState['sisty']['orders'] = dataRecivedEvent.data['data']
        newState['sisty']['orderbook'] = dict()
        newState['sisty']['orderbook']['bids'] = list()
        newState['sisty']['orderbook']['asks'] = list()
        for order in newState['sisty']['orders']['content']['datas']:
            if order['status'] == 1 or order['status'] == 2:
                if order['type'] == 1:
                    price = order['entrustprice']
                    amount = order['surplusamount']
                    orderId = order['id']
                    newState['sisty']['orderbook']['bids'].append([price, amount, orderId])
                elif order['type'] == 2:
                    price = order['entrustprice']
                    amount = order['surplusamount']
                    orderId = order['id']
                    newState['sisty']['orderbook']['bids'].append([price, amount, orderId])
        return newState

    def tickHandler(self, state, tickEvent):
        newState = dict()
        newState.update(state)
        newState['count'] = state.get('count', 0) + 1

        return newState

    def systemEventHandler(self, state, systemEvent):
        newState = dict()
        newState.update(state)
        # if systemEvent.data['type'] == 'LISTEN_STOPPED':
        #     if systemEvent.data['info']['source'] == state['tickSource']:
        #         newState['tickSource'] = None
        #         newState['tickBackup'] = systemEvent.data['info']['source']
        # elif systemEvent.data['type'] == 'LISTEN_STARTED':
        #     if systemEvent.data['info']['source'] is not None and systemEvent.data['info']['source'] == state.get('tickBackup'):
        #         newState['tickSource'] = systemEvent.data['info']['source']
        #         newState['tickBackup'] = None

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
sistyOrderSource = CycleSource(reactor,sisty.getOrders,key='sistyOrder',payload={
    'args':[('eth','usdt'),-1,[1,2,3,4,5]]
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
    'dataRecivedEvent',
    robot.sistyOrderHandler,
    'sistyOrder'
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
        global TIME
        TIME = time.time()
        print('starting robot service...')
        robot.listen([gateioSource, huobiproSource, sistyOrderSource, tickSource])
        gateioSource.start()
        huobiproSource.start()
        sistyOrderSource.start()
        tickSource.start()

    def stopService(self):
        print('stopping robot service...')
        gateioSource.stop()
        huobiproSource.stop()
        sistyOrderSource.stop()
        tickSource.stop()
