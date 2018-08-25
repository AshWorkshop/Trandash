

import json
import time
import datetime

from twisted.internet import defer, task
from twisted.internet import reactor
from twisted.python.failure import Failure


from utils import calcMean
from exchange import verifyExchanges
from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex
from exchanges.huobi.HuobiproService import huobipro

from exchange import OrderBooks
from cycle.cycle import Cycle
from twisted.python.failure import Failure

startTime = int(time.time())
count = 0
coinPair = ('eth', 'usdt')
orderBooks = OrderBooks(['gateio', 'huobipro'], coinPair)
SELL,BUY = range(2)
EXCHANGE = {
    'huobipro': huobipro,
    'gateio': gateio,
    'bitfinex': bitfinex
}
FEE = {
    'huobipro': [0.998, 1.002],
    'gateio': [0.998, 1.002],
    'bitfinex': [0.998, 1.002],
    'virtual': [1, 1],
}
profit = 0.0
traded_count = 1
sells = 1
buys = 1
pairsDone = 1
balance = 1
#{'eth': 0.06630838, 'usdt': 15.42157944}
#{'usdt': 15.2441271, 'eth': 0.0527240038008}

orderBooks.start(reactor)
state = 'GO'


@defer.inlineCallbacks
def buy(exchange,coinPair,amount,price):
    global buy
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
        buys += 1
        try:
            order = yield exchange.getOrder(orderId,coinPair)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())


#    state = "GO"

@defer.inlineCallbacks
def sell(exchange,coinPair,amount,price):
    global sell
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
        sells += 1
        try:
            order = yield exchange.getOrder(orderId,coinPair)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())

    state = "GO"


def cbRun():
    global count
    global state

    global traded_count
    global pairsDone
    global sell
    global buy
    global balance
    count += 1
    # print(count)
    # time.sleep(1)
    exchangeState = dict()
    mark = {
        "count":count,
        "pairsDone":[pairsDone,pairsDone/count],
        "balance":[balance,balance/pairsDone],
        "traded_count":[traded_count,traded_count/pairsDone,traded_count/balance],
        "sell":[sells,sells/traded_count],
        "buy":[buys,buys/traded_count]
    }
    print(mark)

    hasData = True

    if state == "GO":
        for exchange, slot in orderBooks.slots.items():
            bids, asks = slot.getOrderBook()
            slot.setOrderBook()
            exchangeState[exchange] = dict()
            if len(bids) == 0:
                hasData = False
                break
            avgBids = calcMean(bids) #买单
            avgAsks = calcMean(asks) #卖单

            exchangeState[exchange]['actual'], exchangeState[exchange]['avg'] = [bids, asks], [avgBids, avgAsks]
        #print(HuobiBalancesCycle.getData())
        #print(exchangeState)
        #print(GateioBalancesCycle.getData())

        if hasData:
            exchangePairs = verifyExchanges(exchangeState,FEE)
            print(count, exchangePairs)

            if exchangePairs:
                pairsDone += 1
                state = "GO"
                amount = exchangePairs[0][2][1]*0.1
                exBuy = EXCHANGE[exchangePairs[0][0][BUY]]
                priceBuy  = exchangePairs[0][1][BUY]
                #print(exchange.getBalance('usdt'),price,amount)
                exSell = EXCHANGE[exchangePairs[0][0][SELL]]
                priceSell  = exchangePairs[0][1][SELL]
                exBalanceSell = 0.0
                exBalanceBuy = 0.0

                balanceSell = BALANCES[exchangePairs[0][0][SELL]].getData()
                balanceBuy = BALANCES[exchangePairs[0][0][BUY]].getData()

                print(balanceSell,balanceBuy)
                if isinstance(balanceSell,dict) and isinstance(balanceBuy,dict):
                    balance += 1
                    exBalanceSell = balanceSell[coinPair[SELL]]
                    exBalanceBuy = balanceBuy[coinPair[BUY]]
                    usdtAmount = balanceBuy[coinPair[BUY]]+balanceSell[coinPair[BUY]]

                #print(isinstance(exBalanceSell,float),isinstance(exBalanceBuy,float))
                #print("SELL",exBalanceSell,"BUY",exBalanceBuy)
                #print(amount,amount*priceBuy)

                if isinstance(exBalanceSell,float) and isinstance(exBalanceBuy,float):
                    if amount <= exBalanceSell and amount*priceBuy <= exBalanceBuy:
                        amount = amount*0.01
                        reactor.callWhenRunning(buy,exchange=exBuy,coinPair=orderBooks.pairs,price=priceBuy,amount=amount)
                        reactor.callWhenRunning(sell,exchange=exSell,coinPair=orderBooks.pairs,price=priceSell,amount=amount)
                        traded_count += 1
                        pairsName = orderBooks.pairs
                        currentTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')#现在
                        staFile = open('gatoio' + 'huobipro' + str(startTime), 'a+')
                        staFile.write("%d, pairsName:%s, currentTime:%s, usdtAmount:%f, traded_count:%d\n" % (count, pairsName,currentTime, usdtAmount, traded_count))
                        staFile.close()
                    else:
                        state = "GO"
                        print("Not enough coin/money")
                else:
                    state = "GO"
                    print("No exchange")

def ebLoopFailed(failure):
    """
    Called when loop execution failed.
    """
    print(failure.getBriefTraceback())
    reactor.stop()

# reactor.callWhenRunning(cbRun)
HuobiBalancesCycle = Cycle(reactor,huobipro.getBalances,'balances',clean = False)
HuobiBalancesCycle.start(list(coinPair))
GateioBalancesCycle = Cycle(reactor,gateio.getBalances,'gateio',clean = False)
GateioBalancesCycle.start(list(coinPair))
BitfinexBalancesCycle = Cycle(reactor,bitfinex.getBalances,'bitfinex',clean = False)
BitfinexBalancesCycle.start(list(coinPair))
BALANCES = {
    'huobipro': HuobiBalancesCycle,
    'gateio': GateioBalancesCycle,
    'bitfinex': BitfinexBalancesCycle
}
loop = task.LoopingCall(cbRun)

loopDeferred = loop.start(1.0)
loopDeferred.addErrback(ebLoopFailed)

reactor.run()
