

import json
import time

from twisted.internet import defer, task
from twisted.internet import reactor
from twisted.python.failure import Failure


from utils import calcMean, getLevel
from exchange import calcVirtualOrderBooks, verifyExchanges
from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex
from exchanges.huobi.HuobiproService import huobipro

from exchange import OrderBooks
from cycle.cycle import Cycle

count = 0
'''initial OrderBooks'''
coinA = 'usdt'  #A2C, C2B -> A2B
coinC = 'eth'
coinB = 'eos'
coinPair1 = ('eth', 'usdt')  #1 2 ->3
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

   state = "GO"

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

        if hasData:
            '''add virtualOrderBook into exchangeSate '''
            virtualOrderBooks = calcVirtualOrderBooks(A, B)
            print('midAmount in virtualOrderBooks:')  
            print(count, virtualOrderBooks[1])
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
            print('validExPairs:')
            print(count, exchangePairs)

            '''
            buy and sell:
            BUY=1, SELL=0
            PRICE=0, AMOUNT=1
            '''
            if exchangePairs:  #skip when exchangePairs is [] or None.
                state = "WAIT"
                '''get midAmount'''
                virtualLevel = exchangePairs[0][2][0]
                midAmountBuy = virtualOrderBooks[1][BUY][virtualLevel]   #get midAmount according to virtual Level
                midAmountSell = virtualOrderBooks[1][SELL][virtualLevel] #get midAmount according to virtual Level
                '''get each balance'''
                balanceA = 0.0  #balance of 'usdt'
                balanceC = 0.0  #balance of 'eth'
                balanceB = 0.0  #balance of 'eos'                
                balances = BALANCES[exchangeName].getData()
                if isinstance(balancec,dict):
                    balanceA = balances[coinA]  #balance of 'usdt'
                    balanceC = balances[coinC]  #balance of 'eth'
                    balanceB = balances[coinB]  #balance of 'eos'
                exchange = EXCHANGE[exchangeName]  #original exchange instance, eg bitfinex
                
                '''do buy '''
                print('do: BUY')
                strExchange = exchangePairs[0][0][BUY]

                '''do buy in two trade districts:'''
                if strExchange == 'virtual':
                    #first, in orderBookA: eth-usdt
                    amountBuyA = midAmountBuy
                    levelA = getLevel(amountBuyA,A[BUY])
                    priceBuyA = A[BUY][levelA][PRICE]                    
                    #second, in orderBookB: eos-eth
                    amountBuyB = exchangePairs[0][2][1]  
                    levelB = getLevel(amountBuyB,B[BUY])
                    priceBuyB = B[BUY][levelB][PRICE]

                    if isinstance(balanceA,float) and isinstance(balanceC,float):
                        if amountBuyA*priceBuyA <= balanceA and amountBuyB*priceBuyB <= balanceC:
                            print(balances)
                            reactor.callWhenRunning(buy,exchange=exchange,coinPair=orderBooksA.pairs,price=priceBuyA,amount=amountBuyA)
                            reactor.callWhenRunning(buy,exchange=exchange,coinPair=orderBooksB.pairs,price=priceBuyB,amount=amountBuyB)
                        else:
                            state = "GO"
                            print("Not enough coin/money")
                    else:
                        state = "GO"
                        print("No exchange")  
                    
                '''do buy in real district:orderBooks: eos-usdt'''
                else:
                    priceBuy = exchangePairs[0][1][BUY]
                    amountBuy = exchangePairs[0][2][1]
                    print(type(priceBuy))
                    print(type(amountBuy))
                    if isinstance(balanceA,float):
                        if amountBuy*priceBuy <= balanceA:
                            print(balances)
                            reactor.callWhenRunning(buy,exchange=exchange,coinPair=orderBooks.pairs,price=priceBuy,amount=amountBuy)
                        else:
                            state = "GO"
                            print("Not enough coin/money")
                    else:
                        state = "GO"
                        print("No exchange")

                
                '''do sell '''
                print('do: SELL')
                strExchange = exchangePairs[0][0][SELL]

                '''do sell in two trade districts:'''
                if strExchange == 'virtual':
                    #first, in orderBookB: eos-eth
                    amountSellB = exchangePairs[0][2][1]  
                    levelB = getLevel(amountSellB,B[SELL])
                    priceSellB = B[SELL][levelB][PRICE]
                    #second, in orderBookA: eth-usdt
                    amountSellA = midAmountSell
                    levelA = getLevel(amountSellA,A[SELL])
                    priceSellA = A[SELL][levelA][PRICE]

                    if isinstance(balanceB,float) and isinstance(balanceC,float):
                        if amountSellB <= balanceB and amountSellA <= balanceC:
                            print(balances)
                            reactor.callWhenRunning(sell,exchange=exchange,coinPair=orderBooksB.pairs,price=priceSellB,amount=amountSellB)
                            reactor.callWhenRunning(sell,exchange=exchange,coinPair=orderBooksA.pairs,price=priceSellA,amount=amountSellA)
                        else:
                            state = "GO"
                            print("Not enough coin/money")
                    else:
                        state = "GO"
                        print("No exchange")                   

                '''do sell in real district:orderBooks: eos-usdt'''
                else:
                    priceSell = exchangePairs[0][1][SELL]
                    amountSell = exchangePairs[0][2][1]
                    print(type(priceSell))
                    print(type(amountSell))
                    if isinstance(balanceB,float):
                        if amountSell*priceSell <= balanceB:
                            print(balances)
                            reactor.callWhenRunning(sell,exchange=exchange,coinPair=orderBooks.pairs,price=priceSell,amount=amountSell)
                        else:
                            state = "GO"
                            print("Not enough coin/money")
                    else:
                        state = "GO"
                        print("No exchange")


    # yield cbRun()
def ebLoopFailed(failure):
    """
    Called when loop execution failed.
    """
    print(failure.getBriefTraceback())
    reactor.stop()

# reactor.callWhenRunning(cbRun)

coinList = [coinA, coinC, coinB]  #A,C,B | A2C,C2B -> A2B
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