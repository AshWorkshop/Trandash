

import json
import time

from twisted.internet import defer, task
from twisted.internet import reactor
from twisted.python.failure import Failure
from requestUtils.request import get
from utils import calcMean, getLevel
from exchange import calcVirtualOrderBooks, verifyExchanges
from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex
from exchanges.huobi.HuobiproService import huobipro

from exchange import OrderBooks

count = 0
'''initial OrderBooks'''
orderBooks = OrderBooks( ['bitfinex'], ('eos', 'usdt'))
orderBooks.start(reactor)
orderBookA = OrderBooks( ['bitfinex'], ('eth', 'usdt'))
orderBookA.start(reactor)
orderBookB = OrderBooks( ['bitfinex'], ('eos', 'eth'))
orderBookB.start(reactor)
state = 'FIRST'

EXCHANGE = {
    'huobipro': huobipro,
    'gateio': gateio,
    'bitfinex': bitfinex
}
FEE = {
    'huobipro': [1.004, 0.996],
    'gateio': [1.004, 0.996],
    'bitfinex': [1.004, 0.996],
    'virtual': [1.004, 0.996],
}
SELL, BUY = range(2)
PRICE, AMOUNT = range(2)

'''api'''
@defer.inlineCallbacks
def buy(exchange,coinPair,amount,price):
    print(exchange,amount,price)
    print(exchange.getBalance(coinPair(BUY)))
    orderId = None
    if exchange.getBalance(coinPair[BUY]) >= price*amount:
        try:
            orderId = yield exchange.buy(coinPair,price,amount)
            print(orderId)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())

    if orderId[0] == True:
        print("SUCCESSFULLY BUY:", orderId[1])
        try:
            order = yield exchange.getOrder(orderId,coinPair)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())

    state = "GO"

@defer.inlineCallbacks
def sell(exchange,coinPair,amount,price):
    global state
    orderId = None
    if exchange.getBalance(coinPair[SELL]) >= amount:
        try:
            orderId = yield exchange.sell(coinPair,price,amount)
            print(orderId)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())

    if orderId[0] == True:
        print("SUCCESSFULLY SELL:", orderId[1])
        try:
            order = yield exchange.getOrder(orderId,coinPair)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())

    state = "GO"

def cbRun():
    global count
    count += 1
    # print(count)
    # time.sleep(1)
    exchangeState = dict()

    hasData = True
    
    '''get orderBookA'''
    A = []
    for exchange, slot in orderBookA.slots.items():
        bids, asks = slot.getOrderBook()
        slot.setOrderBook()
        if len(bids) == 0:
            hasData = False
            break
        A = [bids, asks]

    '''get orderBookB'''
    B = []
    for exchange, slot in orderBookB.slots.items():
        bids, asks = slot.getOrderBook()
        slot.setOrderBook()
        if len(bids) == 0:
            hasData = False
            break   
        B = [bids, asks] 
        # print(B)

    '''get origin orderBook'''
    for exchange, slot in orderBooks.slots.items():
        bids, asks = slot.getOrderBook()
        slot.setOrderBook()
        exchangeState[exchange] = dict()
        if len(bids) == 0:
            hasData = False
            break
        avgBids = calcMean(bids)
        avgAsks = calcMean(asks)

        exchangeState[exchange]['actual'], exchangeState[exchange]['avg'] = [bids, asks], [avgBids, avgAsks]

    # print(exchangeState)

    if hasData:
        '''add virtualOrderBook into exchangeSate '''
        virtualOrderBooks = calcVirtualOrderBooks(A, B)  
        # print(count, virtualOrderBooks)

        vBUY, vSELL = range(2)
        virBids = virtualOrderBooks[0][vBUY]
        virAsks = virtualOrderBooks[0][vSELL]
        # print(len(virBids))
        # print(len(virAsks))
        # print(len(B[0]))
        avgVirBids = calcMean(virBids)
        avgVirAsks = calcMean(virAsks)
        exchangeState['virtual'] = dict()
        exchangeState['virtual']['actual'], exchangeState['virtual']['avg'] = [virBids, virAsks], [avgVirBids, avgVirAsks]
        
        '''get validExPairs '''
        exchangePairs = verifyExchanges(exchangeState)
        print(count, exchangePairs)

        '''possible approaches to get price and amount:
        
        midAmount = virtualOrderBooks['midAmount']
        amountA = midAmount
        levelA = getLevel(amountA, A[0or1])
        priceA = A[0or1][levelA][PRICE]
        
        amountB = exchangePairs[0][2][1]
        levelB = getLevel(amountB, B[0or1])
        priceB = B[0or1][levelB][PRICE]
        '''

        '''buy and sell '''
        if exchangePairs:  #skip when exchangePairs is [] or None.
            print('BUY')
            strExchange = exchangePairs[0][0][BUY]
            if strExchange == 'virtual':
                exchange = EXCHANGE[exchangePairs[0][0][SELL]]
                #TO DO 
            # exchange = EXCHANGE[strExchange]
            # price  = exchangePairs[0][1][BUY]
            # amount = exchangePairs[0][2][1]
            # #print(exchange.getBalance('usdt'),price,amount)
            # reactor.callWhenRunning(buy,exchange=exchange,coinPair=orderBooks.pairs,price=price,amount=amount)

            print('SELL')
            strExchange = exchangePairs[0][0][SELL]
            if strExchange == 'virtual':
                exchange = EXCHANGE[exchangePairs[0][0][BUY]]
                #TO DO
            
            # price  = exchangePairs[0][1][SELL]
            # amount = exchangePairs[0][2][1]
            # reactor.callWhenRunning(sell,exchange=exchange,coinPair=orderBooks.pairs,price=price,amount=amount)

    # yield cbRun()
def ebLoopFailed(failure):
    """
    Called when loop execution failed.
    """
    print(failure.getBriefTraceback())
    reactor.stop()

# reactor.callWhenRunning(cbRun)
loop = task.LoopingCall(cbRun)

loopDeferred = loop.start(1.0)
loopDeferred.addErrback(ebLoopFailed)

reactor.run()