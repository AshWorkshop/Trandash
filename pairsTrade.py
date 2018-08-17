

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
from cycle.cycle import Cycle

count = 0
'''initial OrderBooks'''
coinPair1 = ('eth', 'usdt') #1 2 →3
coinPair2 = ('eos', 'eth')
coinPair3 = ('eos', 'usdt')
exchangeName = 'bitfinex'
orderBooks = OrderBooks( [exchangeName], coinPair3)
orderBooks.start(reactor)
orderBookA = OrderBooks( [exchangeName], coinPair1)
orderBookA.start(reactor)
orderBookB = OrderBooks( [exchangeName], coinPair2)
orderBookB.start(reactor)

SELL, BUY = range(2)
PRICE, AMOUNT = range(2)
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
state = 'GO'


'''api'''
@defer.inlineCallbacks
def buy(exchange,coinPair,amount,price):
    global state
    orderId = None

    if True:#balance >= price*amount:
        try:
            orderId = yield exchange.buy(coinPair,price,amount)
            print(orderId)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())

    if orderId[1] is not None and orderId[0] == True:
        print("SUCCESSFULLY BUY:", orderId[1])
        try:
            order = yield exchange.getOrder(orderId,coinPair)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())

#    state = "GO"

@defer.inlineCallbacks
def sell(exchange,coinPair,amount,price):
    global state
    orderId = None

    if True:#balance >= amount:
        try:
            orderId = yield exchange.sell(coinPair,price,amount)
            print(orderId)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())

    if orderId[1] is not None and orderId[0] == True:
        print("SUCCESSFULLY SELL:", orderId[1])
        try:
            order = yield exchange.getOrder(orderId,coinPair)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())

    state = "GO"

def cbRun():
    global count
    global state
    count += 1
    # print(count)
    # time.sleep(1)
    exchangeState = dict()

    hasData = True

    if state == "GO":
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
            print(count, virtualOrderBooks)
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

            '''
            buy and sell 
            BUY=1, SELL=0
            '''
            if exchangePairs:  #skip when exchangePairs is [] or None.
                state = "WAIT"
                '''get midAmount'''
                virtualLevel = exchangePairs[0][2][0]
                midAmountBuy = virtualOrderBooks[1][BUY][virtualLevel]   #get midAmount according to virtual Level
                midAmountSell = virtualOrderBooks[1][SELL][virtualLevel] #get midAmount according to virtual Level
                balanceA = 0.0  #balance of 'usdt'
                balanceC = 0.0  #balance of 'eth'
                balanceB = 0.0  #balance of 'eos'
                exchange = EXCHANGE[exchangeName]  #origin exchanges, eg bitfinex
                balances = BALANCES[exchangeName].getData()
                if isinstance(balancec,dict):
                    balanceA = balances[coinA]  #balance of 'usdt'
                    balanceC = balances[coinC]  #balance of 'eth'
                    balanceB = balances[coinB]  #balance of 'eos'
                '''do buy and sell '''
                print('do: BUY')
                strExchange = exchangePairs[0][0][BUY]
                if strExchange == 'virtual':
                    exchange = EXCHANGE[exchangePairs[0][0][SELL]] #origin exchanges, eg bitfinex
                    #TO DO 
                # exchange = EXCHANGE[strExchange]
                # price  = exchangePairs[0][1][BUY]
                # amount = exchangePairs[0][2][1]
                # #print(exchange.getBalance('usdt'),price,amount)
                # reactor.callWhenRunning(buy,exchange=exchange,coinPair=orderBooks.pairs,price=price,amount=amount)
                else:
                 


                print('do: SELL')
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
coinA = 'usdt'
coinC = 'eth'
coinB = 'eos'
coinList = [coinA, coinC, coinB]  #A,C,B .A2C,C2B -- A2B
coinPair = ('usdt', 'eth')
HuobiBalancesCycle = Cycle(reactor,huobipro.getBalances,'balances')
HuobiBalancesCycle.start(list(coinPair))
GateioBalancesCycle = Cycle(reactor,gateio.getBalances,'gateio')
GateioBalancesCycle.start(list(coinPair))
BitfinexBalancesCycle = Cycle(reactor,bitfinex.getBalances,'balances')
BitfinexBalancesCycle.start(coinList)
BALANCES = {
    'huobipro': HuobiBalancesCycle,
    'gateio': GateioBalancesCycle,
    'bitfinex': BitfinexBalancesCycle
}
loop = task.LoopingCall(cbRun)

loopDeferred = loop.start(1.0)
loopDeferred.addErrback(ebLoopFailed)

reactor.run()