

import json
import time
import datetime
import shelve
import sys
from sys import argv

from twisted.internet import defer, task
from twisted.internet import reactor
from twisted.python.failure import Failure


from utils import calcMean, getLevel
from exchange import calcVirtualOrderBooks, verifyExchanges, verifyExchangesOne
from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex
from exchanges.huobi.HuobiproService import huobipro

from exchange import OrderBooks
from cycle.cycle import Cycle
from btf_midPairs import hasList, midList, getPairs, getCoinList

# if len(argv) == 4:
#     _, coin, money, dataFile = argv
# else:
#     print("ERROR!")
#     quit()

count = 0
wait = 0
usdtAmount = 0.0
traded_count = 0
# valid_pair_count = 0
startTime = int(time.time())
'''initial OrderBooks'''
exchangeName = 'bitfinex'

coinPairs = getPairs() 


SELL, BUY = range(2)
PRICE, AMOUNT = range(2)
EXCHANGE = {
    # 'huobipro': huobipro,
    # 'gateio': gateio,
    'bitfinex': bitfinex
}
FEE = {
    'huobipro': [0.996, 1.004],
    'gateio': [0.996, 1.004],
    'bitfinex': [0.996, 1.004],
    'virtual': [0.996, 1.004],
}
state = 'FIRST'
stateStr = 'Normal'  #use to record state to write in log file
noBalances = 0


'''api'''
@defer.inlineCallbacks
def buy(exchange,coinPair,amount,price):
    global state
    global stateStr
    global traded_count
    orderId = None

    if True:#balance >= price*amount:
        try:
            orderId = yield exchange.buy(coinPair,price,amount)
            print(orderId)
            stateStr += '| BUY:' + str(orderId)
        except Exception as err:
            failure = Failure(err)
            stateStr += '| BUY ERROR:' + str(failure.getBriefTraceback())
            print(failure.getBriefTraceback())

    if orderId[1] is not None and orderId[0] == True:
        print("SUCCESSFULLY BUY:", orderId[1])
        stateStr += '| SUCCESSFULLY BUY:' + str(orderId[1])
        traded_count += 1
        try:
            order = yield exchange.getOrder(coinPair,orderId)
        except Exception as err:
            failure = Failure(err)
            stateStr += '| getOrder ERROR:' + str(failure.getBriefTraceback())
            print(failure.getBriefTraceback())

    state = "GO"

@defer.inlineCallbacks
def sell(exchange,coinPair,amount,price):
    global state
    global stateStr
    global traded_count
    orderId = None

    if True:#balance >= amount:
        try:
            orderId = yield exchange.sell(coinPair,price,amount)
            print(orderId)
            stateStr += '| SELL:' + str(orderId)
        except Exception as err:
            failure = Failure(err)
            stateStr += '| SELL ERROR:' + str(failure.getBriefTraceback())
            print(failure.getBriefTraceback())

    if orderId[1] is not None and orderId[0] == True:
        print("SUCCESSFULLY SELL:", orderId[1])
        stateStr += '| SUCCESSFULLY SELL:' + str(orderId[1])
        traded_count += 1
        try:
            order = yield exchange.getOrder(coinPair,orderId)
        except Exception as err:
            failure = Failure(err)
            stateStr += '| getOrder ERROR:' + str(failure.getBriefTraceback())
            print(failure.getBriefTraceback())

    state = "GO"

# def cbRun():
#     '''approach to get every coinA, coinB, coinC'''
#     for pair in coinPairs:
#         coinA = pair[0]
#         coinB = pair[1]
#         coinC = pair[2]

#     # coinA = 'usdt'  #A2C, C2B -> A2B
#     # coinC = 'eth'
#     # coinB = 'eos'
#         coinListp = [coinA, coinC, coinB]  #A,C,B | A2C,C2B -> A2B
#     # coinPair1 = ('eth', 'usdt')  #1 2 ->3
#     # coinPair2 = ('eos', 'eth')
#     # coinPair3 = ('eos', 'usdt')
#         coinPair1 = (coinC, coinA)  #A2C
#         coinPair2 = (coinB, coinC)  #C2B
#         coinPair3 = (coinB, coinA)  #A2B
        
#         if exchangeName == 'bitfinex':
#             if coinA =='usdt':
#                 coinA = 'usd'

#         orderBooks = OrderBooks( [exchangeName], coinPair3)
#         orderBooks.start(reactor)
#         orderBookA = OrderBooks( [exchangeName], coinPair1)
#         orderBookA.start(reactor)
#         orderBookB = OrderBooks( [exchangeName], coinPair2)
#         orderBookB.start(reactor)
#         cbRunPart(orderBooks=orderBooks, orderBookA=orderBookA, orderBookB=orderBookB)

def cbRunPart(orderBooks, orderBookA, orderBookB):
    global count
    global state
    global wait
    global stateStr
    global usdtAmount
    global noBalances
    count += 1
    wait += 1
    # print to file
    
    print('[', count, state, ']')
    # time.sleep(1)
    if state == 'FIRST':
        # data = shelve.open(dataFile)
        # buys = data.get('buys', [])
        # sells = data.get('sells', [])
        # print('buys && sells:', buys, sells)
        # buyAvgPrice, buyAmount = getAvg(buys)
        # sellAvgPrice, sellAmount = getAvg(sells)
        # lastBuyAmount = searchLastAmount(buyAmount)
        # lastSellAmount = searchLastAmount(sellAmount)
        state = 'GO'
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
            
            bid = bids[0]
            ask = asks[0]
            A = [bid, ask]

            # A = [bids, asks]

        '''get orderBookB'''
        B = []
        for exchange, slot in orderBookB.slots.items():
            bids, asks = slot.getOrderBook()
            slot.setOrderBook()
            if len(bids) == 0:
                hasData = False
                break 
            
            bid = bids[0]
            ask = asks[0]
            B = [bid, ask]

            # B = [bids, asks] 
            # print(B)

        '''get origin orderBook'''
        for exchange, slot in orderBooks.slots.items():
            bids, asks = slot.getOrderBook()
            slot.setOrderBook()
            exchangeState[exchange] = dict()
            if len(bids) == 0:
                hasData = False
                break

            bid = bids[0]
            ask = asks[0]
            avgBid = bid
            avgAsk = ask

            # avgBids = calcMean(bids)
            # avgAsks = calcMean(asks)
            
            exchangeState[exchange]['actual'], exchangeState[exchange]['avg'] = [bid, ask], [avgBid, avgAsk]
            # exchangeState[exchange]['actual'], exchangeState[exchange]['avg'] = [bids, asks], [avgBids, avgAsks]

        if hasData:
            state = "WAIT"
            stateStr = ''
            '''add virtualOrderBook into exchangeSate '''
            virtualOrderBooks = calcVirtualOrderBooks(A, B)
            print('midAmount in virtualOrderBooks:')  
            print(count, virtualOrderBooks[1])
            vBUY, vSELL = range(2)
            virBid = virtualOrderBooks[0][vBUY][0]
            virAsk = virtualOrderBooks[0][vSELL][0]
            # virBids = virtualOrderBooks[0][vBUY]
            # virAsks = virtualOrderBooks[0][vSELL]
            # print(len(virBids))
            # print(len(virAsks))
            # print(len(B[0]))
            avgVirBid = virBid
            avgVirAsk = virAsk          
            # avgVirBids = calcMean(virBids)
            # avgVirAsks = calcMean(virAsks)
            exchangeState['virtual'] = dict()

            exchangeState['virtual']['actual'], exchangeState['virtual']['avg'] = [virBid, virAsk], [avgVirBid, avgVirAsk]
            # exchangeState['virtual']['actual'], exchangeState['virtual']['avg'] = [virBids, virAsks], [avgVirBids, avgVirAsks]
            
            '''get validExPairs '''
            exchangePairs = verifyExchangesOne(exchangeState,FEE=FEE)
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
                virtualLevel = exchangePairs[0][2][0]  #可交易对里返回的level值
                virtualBuyList = virtualOrderBooks[1][BUY]
                virtualSellList = virtualOrderBooks[1][SELL]
                midAmountBuy = sum(virtualBuyList[:virtualLevel+1])   #get midAmount according to virtual Level
                midAmountSell = sum(virtualSellList[:virtualLevel+1]) #get midAmount according to virtual Level
                
                '''get each balance'''
                balanceA = 0.0  #balance of 'usdt'
                balanceC = 0.0  #balance of 'eth'
                balanceB = 0.0  #balance of 'eos'   
                balances = BALANCES[exchangeName].getData()
                # balancesWr = str(json.dumps(balances))
                if isinstance(balances,dict):
                    if coinA in balances:
                        balanceA = balances[coinA]  #balance of 'usdt'
                    if coinC in balances: 
                        balanceC = balances[coinC]  #balance of 'eth'
                    if coinB in balances:  
                        balanceB = balances[coinB]  #balance of 'eos'
                else:
                    noBalances += 1
                    # return

                exchange = EXCHANGE[exchangeName]  #original exchange instance, eg bitfinex
                
                '''do buy '''
                print('do: BUY')
                strExchange = exchangePairs[0][0][BUY]

                buy_flag = False
                '''do buy in two trade districts:'''
                if strExchange == 'virtual':
                    #first, in orderBookA: eth-usdt
                    amountBuyA = midAmountBuy
                    levelA = getLevel(amountBuyA,A[BUY])
                    # print(len(A[BUY]))
                    if levelA >= len(A[BUY]):
                        stateStr += '| in orderBookA: eth-usdt levelA_Buy out of range, ' + str(levelA) + ',amountBuyA:' + str(amountBuyA)
                        print(stateStr)
                    else:
                        priceBuyA = A[BUY][levelA][PRICE]                    
                        #second, in orderBookB: eos-eth
                        amountBuyB = exchangePairs[0][2][1]  
                        levelB = getLevel(amountBuyB,B[BUY])
                        if levelB >= len(B[BUY]):
                            stateStr += '| in orderBookB: eos-eth levelB_Buy out of range, ' +str(levelB) + ',amountBuyB:' + str(amountBuyB)
                            print(stateStr)
                        else:                   
                            priceBuyB = B[BUY][levelB][PRICE]
                            print(amountBuyA*priceBuyA)
                            usdtAmount = amountBuyA*priceBuyA
                            if isinstance(balanceA,float) and isinstance(balanceC,float):
                                print(balances)
                                if amountBuyA*priceBuyA <= balanceA:
                                    if amountBuyB*priceBuyB <= balanceC:
                                        # reactor.callWhenRunning(buy,exchange=exchange,coinPair=orderBookA.pairs,price=priceBuyA,amount=amountBuyA)
                                        # time.sleep(1)
                                        # reactor.callWhenRunning(buy,exchange=exchange,coinPair=orderBookB.pairs,price=priceBuyB,amount=amountBuyB)
                                        buy_flag = True
                                        print("SUCCESSFULLY do buy in two trade districts orderBookA,B")
                                        state = "GO"
                                    else:
                                        stateStr += '| Not enough coin/money to buy in orderBookB:' + orderBookB.pairs + ', need coinC:' + str(amountBuyB*priceBuyB)
                                        print("Not enough coin/money to buy in orderBookB: %s, need coinC:%f" % (orderBookB.pairs, amountBuyB*priceBuyB))
                                        state = "GO"
                                else:
                                    stateStr += '| Not enough coin/money to buy in orderBookA:' + orderBookA.pairs + ', need usdt:' + str(amountBuyA*priceBuyA)
                                    print("Not enough coin/money to buy in orderBookA: %s, need usdt:%f" % (orderBookA.pairs, amountBuyA*priceBuyA))
                                    state = "GO"
                            else:
                                print("No exchange in two trade districts")  
                                stateStr += '| No exchange in two trade districts'
                                state = "GO"
                    
                else:
                    '''do buy in real district:orderBooks: eos-usdt'''
                    priceBuy = exchangePairs[0][1][BUY]
                    amountBuy = exchangePairs[0][2][1]
                    print(amountBuy*priceBuy)
                    usdtAmount = amountBuy*priceBuy                    
                    if isinstance(balanceA,float):
                        if amountBuy*priceBuy <= balanceA:
                            # print(balances)
                            # reactor.callWhenRunning(buy,exchange=exchange,coinPair=orderBooks.pairs,price=priceBuy,amount=amountBuy)
                            buy_flag = True
                            print("SUCCESSFULLY do buy in real district:orderBooks: %s" % orderBooks.pairs)
                            state = "GO"
                        else:
                            print("Not enough coin/money to buy in real district:orderBooks: %s, need usdt:%f" % (orderBooks.pairs, amountBuy*priceBuy))
                            stateStr += '| Not enough coin/money to buy in real district:orderBooks:' + orderBooks.pairs + ', need usdt:' + str(amountBuy*priceBuy)
                            state = "GO"
                    else:
                        print("No exchange in real district:orderBooks")
                        stateStr += '| No exchange in real district:orderBooks'
                        state = "GO"

                if buy_flag:
                    '''do sell after buying '''
                    print('do: SELL')
                    strExchange = exchangePairs[0][0][SELL]

                    '''do sell in two trade districts:'''
                    if strExchange == 'virtual':
                        #first, in orderBookB: eos-eth
                        amountSellB = exchangePairs[0][2][1]  
                        levelB = getLevel(amountSellB,B[SELL])
                        if levelB >= len(B[SELL]):
                            stateStr += '| levelB_Sell out of range, ' + str(levelB) + ',amountSellB:' + str(amountSellB)
                            print(stateStr)                        
                        else:
                            priceSellB = B[SELL][levelB][PRICE]
                            #second, in orderBookA: eth-usdt
                            amountSellA = midAmountSell
                            levelA = getLevel(amountSellA,A[SELL])
                            if levelA >= len(A[SELL]):
                                stateStr += '| levelA_Sell out of range, ' + str(levelA) + ',amountSellA:' + str(amountSellA)
                                print(stateStr)
                            else:
                                priceSellA = A[SELL][levelA][PRICE]
                                if isinstance(balanceB,float) and isinstance(balanceC,float):
                                    print(balances)
                                    if amountSellB <= balanceB:                      
                                        if amountSellA <= balanceC:
                                            # reactor.callWhenRunning(sell,exchange=exchange,coinPair=orderBookB.pairs,price=priceSellB,amount=amountSellB)
                                            # time.sleep(1)
                                            # reactor.callWhenRunning(sell,exchange=exchange,coinPair=orderBookA.pairs,price=priceSellA,amount=amountSellA)
                                            print("SUCCESSFULLY do sell in real district:orderBooks: %s" % orderBooks.pairs)
                                            state = "GO"
                                        else:
                                            stateStr += '| Not enough coin/money to sell in orderBookA:' + orderBookA.pairs + ', need coinC:' + str(amountSellA)
                                            print("Not enough coin/money to sell in orderBookA: %s, need coinC:%f" % (orderBookA.pairs, amountSellA))
                                            state = "GO"                                                                                  
                                    else:
                                        stateStr += '| Not enough coin/money to sell in orderBookB:' + orderBookB.pairs + ', need coinB:' + str(amountSellB)
                                        print("Not enough coin/money to buy in orderBookB: %s, need coinB:%f" % (orderBookB.pairs, amountSellB))
                                        state = "GO"                                        
                                else:
                                    print("No exchange")
                                    stateStr += '| No exchange in two trade districts'  
                                    state = "GO"                 

                    
                    else:
                        '''do sell in real district:orderBooks: eos-usdt'''
                        priceSell = exchangePairs[0][1][SELL]
                        amountSell = exchangePairs[0][2][1]
                        if isinstance(balanceB,float):
                            if amountSell <= balanceB:
                                # print(balances)
                                # reactor.callWhenRunning(sell,exchange=exchange,coinPair=orderBooks.pairs,price=priceSell,amount=amountSell)
                                print("SUCCESSFULLY do sell in real district:orderBooks: %s" % orderBooks.pairs)
                                state = "GO"                                
                            else:
                                print("Not enough coin/money to sell in real district:orderBooks: %s, need coinB:%f" % (orderBooks.pairs, amountSell))
                                stateStr += '| Not enough coin/money to sell in real district:orderBooks:' + orderBooks.pairs + ', need coinB:' + str(amountSell)
                                state = "GO"
                        else:
                            print("No exchange in real district:orderBooks")
                            stateStr += '| No exchange in real district:orderBooks'
                            state = "GO"
                else:
                    stateStr += '| Not buy, so not do sell'
                    print("Not buy, so not do sell")
                    state = "GO"

                '''data log'''
                # balances = BALANCES[exchangeName].getData() 
                print(balances) 
                balancesWr = str(json.dumps(balances))
                pairsName = orderBookB.pairs+ ' ' + orderBookA.pairs
                currentTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')#现在
                staFile = open('bitfinex_' + '_balances_' + str(startTime), 'a+')
                staFile.write("%d, pairsName:%s, balances:%s, %s, stateStr:%s, usdtAmount:%f, noBalances_count:%d, traded_count:%d\n" % (count, pairsName, balancesWr, currentTime, stateStr, usdtAmount, noBalances, traded_count))
                staFile.close()
                state = "GO"

            else:
                state = "GO"
        else:
            state = "GO"

    # yield cbRun()
def ebLoopFailed(failure):
    """
    Called when loop execution failed.
    """
    print(failure.getBriefTraceback())
    reactor.stop()

# reactor.callWhenRunning(cbRun)


# coinPair = ('usdt', 'eth')
# HuobiBalancesCycle = Cycle(reactor,huobipro.getBalances,'balances',clean=False)
# HuobiBalancesCycle.start(list(coinPair))
# GateioBalancesCycle = Cycle(reactor,gateio.getBalances,'gateio',clean=False)
# GateioBalancesCycle.start(list(coinPair))
coinList = getCoinList()
BitfinexBalancesCycle = Cycle(reactor,bitfinex.getBalances,'balances',clean=False)
BitfinexBalancesCycle.start(coinList)
BALANCES = {
    'huobipro': None,
    'gateio': None,
    'bitfinex': BitfinexBalancesCycle
}

'''approach to get every coinA, coinB, coinC'''
for pair in coinPairs:
    coinA = pair[0]
    coinB = pair[1]
    coinC = pair[2]

    # coinA = 'usdt'  #A2C, C2B -> A2B
    # coinC = 'eth'
    # coinB = 'eos'
    coinListp = [coinA, coinC, coinB]  #A,C,B | A2C,C2B -> A2B
    # coinPair1 = ('eth', 'usdt')  #1 2 ->3
    # coinPair2 = ('eos', 'eth')
    # coinPair3 = ('eos', 'usdt')
    coinPair1 = (coinC, coinA)  #A2C
    coinPair2 = (coinB, coinC)  #C2B
    coinPair3 = (coinB, coinA)  #A2B
    
    if exchangeName == 'bitfinex':
        if coinA =='usdt':
            coinA = 'usd'

    orderBooks = OrderBooks( [exchangeName], coinPair3)
    orderBooks.start(reactor)
    orderBookA = OrderBooks( [exchangeName], coinPair1)
    orderBookA.start(reactor)
    orderBookB = OrderBooks( [exchangeName], coinPair2)
    orderBookB.start(reactor)
    # cbRunPart(orderBooks=orderBooks, orderBookA=orderBookA, orderBookB=orderBookB)

    loop = task.LoopingCall(cbRunPart(orderBooks=orderBooks, orderBookA=orderBookA, orderBookB=orderBookB))

    loopDeferred = loop.start(1.0)
    loopDeferred.addErrback(ebLoopFailed)

reactor.run()