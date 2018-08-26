from robots.base import RobotBase, CycleSource, Action, LoopSource
from twisted.internet import reactor, task
from twisted.application import service
from exchanges.gateio.GateIOService import gateio
from exchanges.huobi.HuobiproService import huobipro
from exchanges.sisty.SistyService import sisty
from exchanges.bitfinex.BitfinexService import bitfinex

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
}

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

def cutOrderBook(orderBook, capacity=1, hasID=False):
    #orderBook: one of bids or asks (type: list)
    #return: cuttedOrderBook, also one of  bids or asks (list of: [price1, capacity],...,[priceN, remainAmount])
    cuttedOrderBook = list()

    ORDERID = 2
    for data in orderBook:
        remainAmount = data[AMOUNT]
        while remainAmount >= capacity:
            remainAmount -= capacity
            if hasID:
                cuttedOrderBook.append([data[PRICE], capacity, data[ORDERID]])
            else:
                cuttedOrderBook.append([data[PRICE], capacity])
        if remainAmount != 0:
            if hasID:
                cuttedOrderBook.append([data[PRICE], remainAmount, data[ORDERID]])
            else:
                cuttedOrderBook.append([data[PRICE], remainAmount])

    return cuttedOrderBook

def mergeOrderBook(orderBook, capacity=1, hasID=True):
    #orderBook: one of bids or asks (type: list) ps:including orderId
    #return: mergedOrderBook, also one of  bids or asks 
    #return: list of: [price1, amount1, [orderIdList1]],...,[priceN, amountN, [orderIdListN]]
    mergedOrderBook = list()
    
    ORDERID = 2
    level = 0
    count = 0
    lenth = len(orderBook)
    while level < lenth:
        amount = orderBook[level][AMOUNT]
        if hasID:
            orderIdList = list()
            orderIdList.append(orderBook[level][ORDERID])
            count = level
            while count+1 < lenth and orderBook[count][PRICE] == orderBook[count+1][PRICE]:
                amount += orderBook[count+1][AMOUNT]
                orderIdList.append(orderBook[count+1][ORDERID])
                count += 1
            mergedOrderBook.append([orderBook[count][PRICE], amount, orderIdList])
            level = count+1
        else:
            count = level
            while count+1 < lenth and orderBook[count][PRICE] == orderBook[count+1][PRICE]:
                amount += orderBook[count+1][AMOUNT]
                count += 1
            mergedOrderBook.append([orderBook[count][PRICE], amount])
            level = count+1            

    return mergedOrderBook

def adjustOrderBook(newState, capacity=1):
    """    
    思路2：将old深度表合并成“价格唯一，数量求和”的合并表，(用mergeOrderBook()函数)
    直接拿这份表和目标深度n表对比，比较价格：
    1.若n中有o中没有的价格，则以相应数量和价格挂单；
    2.若n中有o中有的价格，则比较o总量和n总量，以差量挂撤；
    3.若n中无o中有的价格，则把全部价格等于此价格的单撤掉。
    return: adjustmentDict ; eg:
    { 'bids': [[276, 1], [276, 1], [274, 1], [274, 1], [274,1], ....], 
      'asks':[[278, 1], [278, 0.5], ...], 
      'cancle':[1357684 (# orderId), 1357898, ...]}
    """
    adjustmentDict = dict()
    adjustmentDict['bids'] = list()
    adjustmentDict['asks'] = list()
    adjustmentDict['cancle'] = list()
    ORDERID = 2
    nBids = newState['orderbooks']['bids']
    nAsks = newState['orderbooks']['asks']
    oBids = newState['sisty']['orderbook']['bids']  #including orderId in each level
    oAsks = newState['sisty']['orderbook']['asks']  #including orderId in each level
    mergedBids = mergeOrderBook(oBids)  #including orderIdList in each level
    mergedAsks = mergeOrderBook(oAsks)  #including orderIdList in each level
    notCuttedBids = list()
    notCuttedAsks = list()
    cancleBidsList = list()
    cancleAsksList = list()

    """
    bids: price from high to low
    """
    oBidPrices = list()
    for oBid in mergedBids:
        oBidPrices.append(mergedBids[PRICE])
    nBidPrices = list()
    for nBid in nBids:
        nBidPrices.append(nBid[PRICE])    

    for n in range(len(nBids)):
        """
        1.若n中有 o中没有 的价格，则以相应数量和价格挂单；
        """
        if nBidPrices[n] not in oBidPrices:
            notCuttedBids.append([nBids[n][PRICE], nBids[n][AMOUNT]])
        """
        2.若n中有 o中有 的价格，则比较o总量和n总量，以差量挂撤；
        """
        if nBidPrices[n] in oBidPrices:
            oIndex = oBidPrices.index(nBidPrices[n])
            if nBids[n][AMOUNT] > mergedBids[oIndex][AMOUNT]:
                deltaAmount = nBids[n][AMOUNT] - mergedBids[oIndex][AMOUNT]
                notCuttedBids.append([nBids[n][PRICE], deltaAmount])
            elif nBids[n][AMOUNT] < mergedBids[oIndex][AMOUNT]:
                deltaAmount = mergedBids[oIndex][AMOUNT] - nBids[n][AMOUNT]
                cancleBidsList.append([nBids[n][PRICE], deltaAmount])
    """
    3.若n中无 o中有 的价格，则把全部价格等于此价格的单撤掉。
    """            
    for o in range(len(mergedBids)):
        if oBidPrices[o] not in nBidPrices:
            cancleBidsList.append([mergedBids[o][PRICE], mergedBids[o][AMOUNT]])
    print(cancleBidsList)
   
    """
    处理撤单
    TO DO: sort cancleBidsList to let it: price from high to low
    """ 
    mini = 0
    for i in range(len(cancleBidsList)):
        decimal = cancleBidsList[i][AMOUNT] % capacity
        remainAmount = cancleBidsList[i][AMOUNT]
        if decimal == 0:
            oBids = oBids 
            """            
            TO DO: sort oBids to let it:
            1.price from high to low
            2.amount from high to low
            """
        else: 
            oBids = oBids 
            """            
            TO DO: sort oBids to let it:
            1.price from high to low
            2.amount from low to high
            """
        for j in range(mini, len(oBids)):
            if oBids[j][PRICE] == cancleBidsList[i][PRICE]:
                if remainAmount > 0:
                    orderId = oBids[j][ORDERID] 
                    adjustmentDict['cancle'].append(orderId)
                    remainAmount -= oBids[j][AMOUNT]
                elif remainAmount == 0:
                    mini = j
                    break
                elif remainAmount < 0 and abs(remainAmount) <= capacity:
                    adjustmentDict['bids'].append([oBids[j][PRICE], abs(remainAmount)])
                    mini = j
                    break
                else:
                    raise("handle cancleBidsList error")
    # print("notCuttedBids inner:")
    # print(notCuttedBids)
    # print("cancleBidsList inner:")
    # print(cancleBidsList)
    cuttedBids = cutOrderBook(notCuttedBids)
    adjustmentDict['bids'].extend(cuttedBids)

    """ 
    asks: price from low to high
    """
    oAskPrices = list()
    for oAsk in mergedAsks:
        oAskPrices.append(mergedAsks[PRICE])
    nAskPrices = list()
    for nAsk in nAsks:
        nAskPrices.append(nAsk[PRICE])

    for n in range(len(nAsks)):
        """
        1.若n中有 o中没有 的价格，则以相应数量和价格挂单；
        """
        if nAskPrices[n] not in oAskPrices:
            notCuttedAsks.append([nAsks[n][PRICE], nAsks[n][AMOUNT]])
        """
        2.若n中有 o中有 的价格，则比较o总量和n总量，以差量挂撤；
        """
        if nAskPrices[n] in oAskPrices:
            oIndex = oAskPrices.index(nAskPrices[n])
            if nAsks[n][AMOUNT] > mergedAsks[oIndex][AMOUNT]:
                deltaAmount = nAsks[n][AMOUNT] - mergedAsks[oIndex][AMOUNT]
                notCuttedAsks.append([nAsks[n][PRICE], deltaAmount])
            elif nAsks[n][AMOUNT] < mergedAsks[oIndex][AMOUNT]:
                deltaAmount = mergedAsks[oIndex][AMOUNT] - nAsks[n][AMOUNT]
                cancleAsksList.append([nAsks[n][PRICE], deltaAmount])
    """
    3.若n中无 o中有 的价格，则把全部价格等于此价格的单撤掉。
    """            
    for o in range(len(mergedAsks)):
        if oAskPrices[o] not in nAskPrices:
            cancleAsksList.append([mergedAsks[o][PRICE], mergedAsks[o][AMOUNT]])
    print(cancleAsksList)
   
    """
    处理撤单
    TO DO: sort cancleAsksList to let it: price from low to high
    """ 
    mini = 0
    for i in range(len(cancleAsksList)):
        decimal = cancleAsksList[i][AMOUNT] % capacity
        remainAmount = cancleAsksList[i][AMOUNT]
        if decimal == 0:
            oAsks = oAsks 
            """            
            TO DO: sort oAsks to let it:
            1.price from low to high
            2.amount from high to low
            """
        else: 
            oAsks = oAsks 
            """            
            TO DO: sort oAsks to let it:
            1.price from low to high
            2.amount from low to high
            """
        for j in range(mini, len(oAsks)):
            if oAsks[j][PRICE] == cancleAsksList[i][PRICE]:
                if remainAmount > 0:
                    orderId = oAsks[j][ORDERID] 
                    adjustmentDict['cancle'].append(orderId)
                    remainAmount -= oAsks[j][AMOUNT]
                elif remainAmount == 0:
                    mini = j
                    break
                elif remainAmount < 0 and abs(remainAmount) <= capacity:
                    adjustmentDict['asks'].append([oAsks[j][PRICE], abs(remainAmount)])
                    mini = j
                    break
                else:
                    raise("handle cancleBidsList error")

    # print("notCuttedAsks inner:")
    # print(notCuttedAsks)
    # print("cancleAsksList inner:")
    # print(cancleAsksList)
    cuttedAsks = cutOrderBook(notCuttedAsks)
    adjustmentDict['asks'].extend(cuttedAsks)

    return adjustmentDict

{'id': '535e96c6-9385-4b39-be93-05e929140b3d', 'userid': 222, 'coinid': 36, 'type': 1, #买
'entrustprice': 300.0, 'dealsumprice': 280.32516,
'amount': 1.0, 'status': 3, 'createtime': 1535247027, 'endtime': 1535247116, 'remark': '添加交易买委托单',
'alternatefield': 69, 'surplusamount': 0.0, 'entrustsource': 'APP', 'dealstatus': None},

class TestRobot(RobotBase):
    def launch(self, oldState, newState):
        global TIME
        actions = []
        print(newState)

        if 'sisty' in newState and 'sisty' in oldState:

            old = oldState['sisty']['orders']['content']
            new = newState['sisty']['orders']['content']

            oldOrders = old['datas']
            newOrders = new['datas']

            for orderA in oldOrders:
                for orderB in newOrders:
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
                            for orderC in newState[book]:
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


        #print(newState['data']['content']['datas'])

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

    def sistyOrderHandler(self,state,dataRecivedEvent):
        newState = dict()
        newState.update(state)
        newState['ststy'] = dict()
        newState['sisty'] = state.get('sisty',dict())
        newState['sisty']['orders'] = dataRecivedEvent.data['data']

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
        robot.listen([gateioSource, huobiproSource, sistyOrderSource,tickSource])
        gateioSource.start()
        huobiproSource.start()
        sistyOrderSource.start()
        tickSource.start()

    def stopService(self):
        print('stopping robot service...')
        gateioSource.stop()
        huobiproSource.stop()
        sistyOrderSource.start()
        tickSource.stop()
