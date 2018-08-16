

import json
import time

from twisted.internet import defer, task
from twisted.internet import reactor
from requestUtils.request import get
from utils import calcMean
from exchange import verifyExchanges
from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex
from exchanges.huobi.HuobiproService import huobipro

from exchange import OrderBooks
from cycle.cycle import Cycle

count = 0
coinPair = ('eth', 'usdt')
orderBooks = OrderBooks(['gateio', 'huobipro'], coinPair)
SELL,BUY = range(2)
EXCHANGE = {
    'huobipro': huobipro,
    'gateio': gateio,
    'bitfinex': bitfinex
}

orderBooks.start(reactor)
state = 'GO'


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
            exchangePairs = verifyExchanges(exchangeState)
            print(count, exchangePairs)
            if exchangePairs:
                state = "WAIT"
                amount = 0.005#exchangePairs[0][2][1]
                exBuy = EXCHANGE[exchangePairs[0][0][BUY]]
                priceBuy  = exchangePairs[0][1][BUY]
                #print(exchange.getBalance('usdt'),price,amount)
                exSell = EXCHANGE[exchangePairs[0][0][SELL]]
                priceSell  = exchangePairs[0][1][SELL]
                exBalanceSell = 0.0
                exBalanceBuy = 0.0

                balanceSell = BALANCES[exchangePairs[0][0][SELL]].getData()
                balanceBuy = BALANCES[exchangePairs[0][0][BUY]].getData()

                #print(balanceSell,balanceBuy)
                if isinstance(balanceSell,dict) and isinstance(balanceBuy,dict):
                    exBalanceSell = balanceSell[coinPair[SELL]]
                    exBalanceBuy = balanceBuy[coinPair[BUY]]
                #print(isinstance(exBalanceSell,float),isinstance(exBalanceBuy,float))
                #print("SELL",exBalanceSell,"BUY",exBalanceBuy)
                #print(amount,amount*priceBuy)

                if isinstance(exBalanceSell,float) and isinstance(exBalanceBuy,float):
                    if amount <= exBalanceSell and amount*priceBuy <= exBalanceBuy:
                        reactor.callWhenRunning(buy,exchange=exchange,coinPair=orderBooks.pairs,price=priceBuy,amount=amount)
                        reactor.callWhenRunning(sell,exchange=exchange,coinPair=orderBooks.pairs,price=priceSell,amount=amount)
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
HuobiBalancesCycle = Cycle(reactor,huobipro.getBalances,'balances')
HuobiBalancesCycle.start(list(coinPair))
GateioBalancesCycle = Cycle(reactor,gateio.getBalances,'gateio')
GateioBalancesCycle.start(list(coinPair))
BALANCES = {
    'huobipro': HuobiBalancesCycle,
    'gateio': GateioBalancesCycle,
    'bitfinex': None
}
loop = task.LoopingCall(cbRun)

loopDeferred = loop.start(1.0)
loopDeferred.addErrback(ebLoopFailed)

reactor.run()
