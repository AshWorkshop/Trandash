from exchanges.gateio.GateIOService import gateio
import exchanges.huobi.Huobipro as huobipro
from exchanges.bitfinex.BitfinexService import bitfinex

from twisted.internet import defer

FEE = {
    'huobipro': [0.998, 1.002],
    'gateio': [0.998, 1.002],
    'bitfinex': [0.998, 1.002],
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
        return self.orderBook.copy()

    def setOrderBook(self, orderBook):
        self.orderBook = orderBook.copy()

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
            try:
                orderBook = yield EXCHANGE[exchange].getOrderBook(self.pairs)
            except Exception as err:
                print(err)
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

            # for i, (buy, sell) in enumerate(zip(buyEx['avg'][BUY], sellEx['avg'][SELL])):
            #     # print(buy, sell)
            #     level = i
            #     if buy[PRICE] * FEE[buyExName][BUY] <= sell[PRICE] * FEE[sellExName][SELL]:
            #         level = i - 1
            #         break

            amount = min(buyEx['avg'][BUY][level][AMOUNT], sellEx['avg'][SELL][level][AMOUNT])
            buyPrice = float(buyEx['actual'][BUY][level][PRICE])
            sellPrice = float(sellEx['actual'][SELL][level][PRICE])

            validExPairs.append( ((buyExName, sellExName), (buyPrice, sellPrice), (level, amount)) )

    return validExPairs
