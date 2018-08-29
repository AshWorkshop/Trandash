from robots.base import RobotBase, CycleSource, Action, LoopSource
from twisted.internet import reactor, task
from twisted.application import service
from twisted.logger import Logger
from exchanges.gateio.GateIOService import gateio
from exchanges.huobi.HuobiproService import huobipro
from exchanges.sisty.SistyService import sisty
from exchanges.bitfinex.BitfinexService import bitfinex
from utils import adjustOrderBook,commitOrderBook

import time
import datetime

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
    log = Logger('counter')
    log.info('tick')

class TestRobot(RobotBase):
    def launch(self, oldState, newState):
        global TIME
        actions = []
        #self.log.debug("{newState}", newState=newState)

        self.log.info('failedActions: {number}', number=len(newState.get('failedActions', [])))
        self.log.info('undoneActions: {number}', number=len(newState.get('actions', [])))

        for action in newState['actions']:
            if action.wait:
                return []

        #订单管理
        if 'sisty' in newState:
            if newState['sisty']['orders'] is not None:

                newOrders = newState['sisty']['orders']['content']['datas']

                for order in newOrders:
                    if order['createtime'] < TIME:
                        break
                    orderId = order['id']
                    self.log.debug("{order}", order=order)
                    exchange = None
                    type = None
                    price = None
                    amount = None
                    dealInOrder = order['amount']-order['surplusamount']
                    dealInSource = order.get('dealInSource',0.0)
                    amount = abs(dealInOrder-dealInSource)
                    if amount > 0.000000001:
                        staFile = open('sistyOrderManaged'+str(TIME), 'w+')
                        staFile.write("order:%s\n" % order)
                        staFile.close()
                        if order['type'] == 1:
                            type = "buy"
                        elif order['type'] == 2:
                            type = "sell"
                        if "orderbooks" in newState:
                            if type == "buy":
                                book = "bids"
                            elif type == "sell":
                                book = "asks"
                            for orderC in newState['orderbooks'][book]:
                                if orderC[PRICE] == order['entrustprice']:
                                    price = orderC[PRICE]
                                    exchange = orderC[EXCHANGE]

                    if exchange is not None and type is not None and price is not None and amount is not None:
                        if type == "buy":
                            action = Action(reactor,EXCHANGES[exchange].sell,key=exchange+"M?Sell?"+orderId+"?"+str(amount), wait=True,payload={
                                "args":[coinPairs,price,amount]
                            })
                            staFile = open('sistyOrderManaged'+str(TIME), 'w+')
                            staFile.write("exchange:%s,type:%s,price:%s,amount:%s\n" % (exchange,type,price,amount))
                            staFile.close()
                        if type == "sell":
                            action = Action(reactor,EXCHANGES[exchange].buy,key=exchange+"M?Buy?"+orderId+"?"+str(amount), wait=True,payload={
                                "args":[coinPairs,price,amount]
                            })
                            taFile = open('sistyOrderManaged'+str(TIME), 'w+')
                            staFile.write("exchange:%s,type:%s,price:%s,amount:%s\n" % (exchange,type,price,amount))
                            staFile.close()
                        actions.append(action)
        #调整深度
        if 'orderbooks' in newState and 'sisty' in newState :
            if 'orderbook' in newState['sisty'] and newState['sisty']['orderbook']['bids'] is not None and newState['sisty']['orderbook']['asks'] is not None:
                adjustmentDict = adjustOrderBook(newState, capacity=100)
                self.log.debug("{adjustmentDict}", adjustmentDict=adjustmentDict)
                adjustmentDictStr = str(adjustmentDict)
                currentTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')#现在
                countStr = newState.get('count')
                staFile = open('sisty_' + '_AdjustTest_' + str(TIME), 'a+')
                staFile.write("%s, %s,\n adjustmentDict:\n %s" % (countStr,currentTime,adjustmentDictStr))
                staFile.close()
                exchange = 'sisty'
                if adjustmentDict['bids'] is not None:
                    for bid in adjustmentDict['bids']:
                        price = bid[PRICE]
                        amount = bid[AMOUNT]
                        action = Action(reactor,EXCHANGES[exchange].trade,key='A?Buy?',wait=True,payload={
                                            'args':[coinPairs,price,amount,1]
                                        })
                        actions.append(action)

                if adjustmentDict['asks'] is not None:
                    for ask in adjustmentDict['asks']:
                        price = ask[PRICE]
                        amount = ask[AMOUNT]
                        action = Action(reactor,EXCHANGES[exchange].trade,key='A?Sell?',wait=True,payload={
                                            'args':[coinPairs,price,amount,2]
                                        })
                        actions.append(action)

                if adjustmentDict['cancle'] is not None:
                    for cancleId in adjustmentDict['cancle']:
                        action = Action(reactor,EXCHANGES[exchange].cancle,key=exchange+'cancle',wait=True,payload={
                                            'args':[coinPairs,cancleId]
                                        })
                        actions.append(action)

        #self.log.debug("{data}", data=newState['data']['content']['datas'])

        self.log.info("{count}", count=newState.get('count'))
        # if newState['count'] == 10 and newState.get('tickSource') is not None:
        #     self.log.info('STOP LISTEN TICKEVENT')
        #     self.stopListen(newState['tickSource'])
        #     # newState['tickSource'].stop()
        # if newState['count'] == 15 and newState.get('tickSource') is None:
        #     self.log.info('START LISTEN TICKEVENT')
        #     self.listen(newState['tickBackup'])
        self.log.info('newActions:{actions}', actions=len(actions))
        return actions

    def gateioOrderBookHandler(self, state, dataRecivedEvent):
        print(dataRecivedEvent)
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
        print(dataRecivedEvent)
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
        #print(dataRecivedEvent)
        newState = dict()
        newState.update(state)
        newState['ststy'] = dict()
        newState['sisty'] = state.get('sisty',dict())
        newState['sisty']['orders'] = dataRecivedEvent.data['data']

        newState['sisty']['orderbook'] = dict()
        newState['sisty']['orderbook']['bids'] = list()
        newState['sisty']['orderbook']['asks'] = list()
        if newState['sisty']['orders'] is not None:
            for order in newState['sisty']['orders']['content']['datas']:
                #确保每次sistyOrderHandler的获得的都是全新的newState['sisty']['orderbook']
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
                        newState['sisty']['orderbook']['asks'].append([price, amount, orderId])
                if 'dealInSource' in order:
                    continue
                else:
                    order['dealInSource'] = 0.0        
        return newState

    def actionDoneHandler(self,state,actionDoneEvent):
        exchanges = ['huobiproM','gateioM','bitfinexM']
        EXCHANGE,TYPE,ORDERID,AMOUNT = range(4)
        key = actionDoneEvent.key
        if key is not None:
            keys = key.split("?")
            if keys[EXCHANGE] in exchanges:
                orderId = keys[ORDERID]
                amount = keys[AMOUNT]
                newState = dict()
                newState.update(state)
                if 'sisty' in newState:
                    if newState['sisty']['orders']['content']['datas'] is not None:
                        for order in newState['sisty']['orders']['content']['datas']:
                            if order['id'] == orderId:
                                order['dealInSource'] += amount

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

gateioSource = CycleSource(reactor, gateio.getOrderBook, key='gateioOrderBooks', payload={
    'args': [('eth', 'usdt')]
})
huobiproSource = CycleSource(reactor,huobipro.getOrderBook, key='huobiproOrderBooks',payload={
    'args': [('eth','usdt')]
})
bitfinexSource = CycleSource(reactor,bitfinex.getOrderBook, key='bitfinexOrderBooks',payload={
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
    'gateioOrderBooks'
)
robot.bind(
    'dataRecivedEvent',
    robot.huobiproOrderBookHandler,
    'huobiproOrderBooks'
)
robot.bind(
    'dataRecivedEvent',
    robot.bitfinexOrderBookHandler,
    'bitfinexOrderBooks'
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

robot.bind(
    'actionDoneEvent',
    robot.actionDoneHandler,
)

robot.state.update({
    'tickSource': tickSource,
})

class RobotService(service.Service):
    log = Logger()
    def startService(self):
        global TIME
        TIME = time.time()
        self.log.info('starting robot service...')
        robot.listen([gateioSource, huobiproSource, sistyOrderSource, tickSource])
        gateioSource.start()
        huobiproSource.start()
        sistyOrderSource.start()
        tickSource.start()

    def stopService(self):
        self.log.info('stopping robot service...')
        gateioSource.stop()
        huobiproSource.stop()
        sistyOrderSource.stop()
        tickSource.stop()
