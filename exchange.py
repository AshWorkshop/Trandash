from exchanges.gateio.GateIOService import gateio
from exchanges.huobi.HuobiproService import huobipro
from exchanges.bitfinex.BitfinexService import bitfinex

from twisted.internet import defer
from twisted.python.failure import Failure
import copy

FEE = {
    'huobipro': [1,1],#[0.998, 1.002],
    'gateio': [1,1],#[0.998, 1.002],
    'bitfinex': [1, 1],
    'virtual': [1, 1],
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
        return copy.deepcopy(self.orderBook)

    def setOrderBook(self, orderBook=None):
        if orderBook is None:
            orderBook = [[], []]
        self.orderBook = copy.deepcopy(orderBook)

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

def verifyExchanges(exchangesData, FEE=FEE):
    # index enumeration for taking buy/sell data from exchange tuple
    BUY, SELL = range(2)

    # index enumeration for taking price/amount data from price/amount tuple
    PRICE, AMOUNT = range(2)

    validExPairs = []
    flag = 0
    exchangesAmount = len(exchangesData)
    for buyExName, buyEx in exchangesData.items():
        # print(buyEx)
        for sellExName, sellEx in exchangesData.items():

            if buyExName == sellExName: continue
            flag += 1
            if buyEx['avg'][BUY][0][PRICE] * FEE[buyExName][BUY] <= sellEx['avg'][SELL][0][PRICE] * FEE[sellExName][SELL]: continue

            level = 0
            amount = 0
            maxLevel = min(len(buyEx['actual'][BUY]), len(sellEx['actual'][SELL]))-1
            # print(maxLevel)

            for i, (buy, sell) in enumerate(zip(buyEx['avg'][BUY], sellEx['avg'][SELL])):
                # print(buy, sell)
                level = i
                if buy[PRICE] * FEE[buyExName][BUY] <= sell[PRICE] * FEE[sellExName][SELL]:
                    level = i - 1
                    break
                elif level >= maxLevel:
                    print('error: one of possibility reaches max level when getting validExPairs.')
                    possibilities = exchangesAmount
                    if flag == possibilities:
                        print('error: All possibilities reach max level when getting validExPairs.')
                        return None
                    else:
                        break
            if level >= maxLevel:
                continue

            # print(level)
            amount = min(buyEx['avg'][BUY][level][AMOUNT], sellEx['avg'][SELL][level][AMOUNT])
            buyPrice = float(buyEx['actual'][BUY][level][PRICE])
            sellPrice = float(sellEx['actual'][SELL][level][PRICE])

            validExPairs.append( ((buyExName, sellExName), (buyPrice, sellPrice), (level, amount)) )

    return validExPairs

def calcOneWayVirtualOrderBooks(A2C: ['bids/asks'], C2B: ['bids/asks']):
    """calculate virtual order book from coin A to coin B through coin C"""

    # index enumeration for taking price/amount data from price/amount tuple
    PRICE, AMOUNT = range(2)

    A2C_, C2B_ = copy.deepcopy(A2C), copy.deepcopy(C2B)

    virtualOrderBook = []
    medium = []

    while A2C_ and C2B_:
        # the maximum amount of coin C which purchased all coin A need
        amountA = A2C_[0][PRICE] * A2C_[0][AMOUNT]
        # the maximum amount of coin C which can be purchased with coin B
        amountB = C2B_[0][AMOUNT]
        if amountA == amountB:
            vAmount = A2C_[0][AMOUNT]
            vPrice = C2B_[0][AMOUNT] * C2B_[0][PRICE] / vAmount
            virtualOrderBook.append( [vPrice, vAmount] )
            medium.append(amountA)
            del C2B_[0]
            del A2C_[0]
        elif amountA > amountB:
            vAmount = C2B_[0][AMOUNT] / A2C_[0][PRICE]
            vPrice = C2B_[0][AMOUNT] * C2B_[0][PRICE] / vAmount
            virtualOrderBook.append( [vPrice, vAmount] )
            medium.append(amountB)
            del C2B_[0]
            A2C_[0][AMOUNT] -= vAmount
        else:
            vAmount = A2C_[0][AMOUNT]
            vPrice = A2C_[0][AMOUNT] * A2C_[0][PRICE] * C2B_[0][PRICE] / vAmount
            virtualOrderBook.append( [vPrice, vAmount] )
            medium.append(amountA)
            C2B_[0][AMOUNT] -= A2C_[0][AMOUNT] * A2C_[0][PRICE]
            del A2C_[0]

    return (virtualOrderBook, medium)

def calcVirtualOrderBooks(orderBookA: [['bids'], ['asks']],
                          orderBookB: [['bids'], ['asks']]):
    """calculate virtual order book between coin A and coin B through coin C"""

    # index enumeration for taking buy/sell data from order book list
    BUY, SELL = range(2)

    orderBookBuy, mediumBuy = calcOneWayVirtualOrderBooks(orderBookA[BUY], orderBookB[BUY])
    orderBookSell, mediumSell = calcOneWayVirtualOrderBooks(orderBookA[SELL], orderBookB[SELL])
    return ([orderBookBuy, orderBookSell], [mediumBuy, mediumSell])

if __name__ == '__main__':
    USDT2ETH = [
        [100, 5],
        [110, 5],
        [120, 10],
        [130, 10],
    ]
    ETH2EOS = [
        [0.01, 300],
        [0.02, 500],
        [0.03, 500],
        [0.05, 500],
    ]
    supposedUSDT2EOS = [  #have question
        [1, 300],
        [2, 100],
        [2.2, 250],
        [2.4, 150],
    ]
    supposedMedium = [300*0.01, (300*0.01)+(100*0.02), (300*0.01+100*0.02)+(250*0.02), (300*0.01+100*0.02+250*0.02)+(150*0.02)]
    print(f'USDT2ETH: {USDT2ETH}\nETH2EOS: {ETH2EOS}\nUSDT2EOS: {calcOneWayVirtualOrderBooks(USDT2ETH, ETH2EOS)}')
    print(f'supposed USDT2EOS: {supposedUSDT2EOS, supposedMedium}\n')
