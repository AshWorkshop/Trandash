from exchanges.gateio.GateIOService import gateio
from exchanges.huobi.HuobiproService import huobipro
from exchanges.bitfinex.BitfinexService import bitfinex

from twisted.internet import defer
from twisted.python.failure import Failure

FEE = {
    'huobipro': [0.999, 1.001],
    'gateio': [0.999, 1.001],
    'bitfinex': [0.999, 1.001],
}

EXCHANGE = {
    'huobipro': huobipro,
    'gateio': gateio,
    'bitfinex': bitfinex
}

class Slot(object):

    def __init__(self, exchange, pairs):
        self.exchange = exchange
        self.pairs = pairs
        self.orderBook = [[], []] # [bids, asks]

    def getOrderBook(self):
        return self.orderBook.copy() # WARNING: not deep copy, need fixing

    def setOrderBook(self, orderBook=[[], []]): # WARNING: use list as default parameter, need fixing
        self.orderBook = orderBook.copy() # WARNING: not deep copy, need fixing

class OrderBooks(object):

    def __init__(self, exchanges, pairs):
        self.pairs = pairs
        self.slots = dict()
        self.numSlot = len(exchanges)
        self.running = False
        for exchange in exchanges:
            self.slots[exchange] = Slot(exchange, pairs)

    @defer.inlineCallbacks
    def cbRun(self, exchange):
        if self.running:
            # print('running')
            orderBook = [[], []]
            try:
                orderBook = yield EXCHANGE[exchange].getOrderBook(self.pairs)
            except Exception as err:
                failure = Failure(err)
                print(failure.getBriefTraceback())
            self.slots[exchange].setOrderBook(orderBook)
            # print(orderBook)

            yield self.cbRun(exchange)

    def start(self, reactor):
        self.running = True
        for exchange, slot in self.slots.items():
            reactor.callWhenRunning(self.cbRun, exchange)

    def stop(self):
        self.running = False

    def getOrderBooks(self):
        result = self.slots.copy()
        return result

def verifyExchanges(exchangesData):

    # index enumeration for taking buy/sell data from exchange tuple
    BUY, SELL = range(2)

    # index enumeration for taking price/amount data from price/amount tuple
    PRICE, AMOUNT = range(2)

    validExPairs = []
    for buyExName, buyEx in exchangesData.items():
        # print(buyEx)
        for sellExName, sellEx in exchangesData.items():
            if buyExName == sellExName: continue
            if buyEx['avg'][BUY][0][PRICE] * FEE[buyExName][BUY] <= sellEx['avg'][SELL][0][PRICE] * FEE[sellExName][SELL]: continue

            level = 0
            amount = 0

            for i, (buy, sell) in enumerate(zip(buyEx['avg'][BUY], sellEx['avg'][SELL])):
                # print(buy, sell)
                level = i
                if buy[PRICE] * FEE[buyExName][BUY] <= sell[PRICE] * FEE[sellExName][SELL]:
                    level = i - 1
                    break

            amount = min(buyEx['avg'][BUY][level][AMOUNT], sellEx['avg'][SELL][level][AMOUNT])
            buyPrice = float(buyEx['actual'][BUY][level][PRICE])
            sellPrice = float(sellEx['actual'][SELL][level][PRICE])

            validExPairs.append( ((buyExName, sellExName), (buyPrice, sellPrice), (level, amount)) )

    return validExPairs

def calcOneWayVirtualOrderBooks(A2C: ['bids/asks'], C2B: ['bids/asks']):
    """calculate virtual order book from coin A to coin B through coin C"""

    # index enumeration for taking price/amount data from price/amount tuple
    PRICE, AMOUNT = range(2)

    A2C_, C2B_ = [order.copy() for order in A2C], [order.copy() for order in C2B]

    virtualOrderBook = []

    while A2C_ and C2B_:
        # the maximum amount of coin C which purchased all coin A need
        amountA = float(A2C_[0][PRICE]) * float(A2C_[0][AMOUNT])
        # the maximum amount of coin C which can be purchased with coin B
        amountB = float(C2B_[0][AMOUNT])
        if amountA == amountB:
            vAmount = float(A2C_[0][AMOUNT])
            vPrice = float(C2B_[0][AMOUNT]) * float(C2B_[0][PRICE]) / vAmount
            virtualOrderBook.append( [vPrice, vAmount] )
            del C2B_[0]
            del A2C_[0]
        elif amountA > amountB:
            vAmount = float(C2B_[0][AMOUNT]) / float(A2C_[0][PRICE])
            vPrice = float(C2B_[0][AMOUNT]) * float(C2B_[0][PRICE]) / vAmount
            virtualOrderBook.append( [vPrice, vAmount] )
            del C2B_[0]
            a2c_amount = float(A2C_[0][AMOUNT])
            a2c_amount -= vAmount
            A2C_[0][AMOUNT] = str(a2c_amount)
        else:
            vAmount = float(A2C_[0][AMOUNT])
            vPrice = float(A2C_[0][AMOUNT]) * float(A2C_[0][PRICE]) * float(C2B_[0][PRICE]) / vAmount
            virtualOrderBook.append( [vPrice, vAmount] )
            c2b_amount = float(C2B_[0][AMOUNT])
            c2b_amount -= float(A2C_[0][AMOUNT]) * float(A2C_[0][PRICE])
            C2B_[0][AMOUNT] = str(c2b_amount)
            del A2C_[0]

    return virtualOrderBook

def calcVirtualOrderBooks(orderBookA: [['bids'], ['asks']], 
                          orderBookB: [['bids'], ['asks']]):
    """calculate virtual order book between coin A and coin B through coin C"""

    # index enumeration for taking buy/sell data from order book list
    BUY, SELL = range(2)

    return [
        calcOneWayVirtualOrderBooks(orderBookA[BUY], orderBookB[BUY]),
        calcOneWayVirtualOrderBooks(orderBookA[SELL], orderBookB[SELL])
    ]

