

import json
import time

from twisted.internet import defer
from twisted.internet import reactor
from request import get
from utils import calcMean
from exchange import FEE
from exchanges.gateio.GateIOService import gateio
from exchanges.bitfinex.BitfinexService import bitfinex

count = 0

def verifyExchanges(
        exchangesData: {
            'exchangeName': {
                'avg': (
                    [('buyPriceArgN, handling fee considered, from HIGH to LOW',
                      'buyTotalAmountN'), ],
                    [('sellPriceArgN, handling fee considered, from LOW to HIGH',
                      'sellTotalAmountN'), ]
                ),
                'actual': (
                    [('buyPriceArgN, handling fee considered, from HIGH to LOW',
                      'buyTotalAmountN'), ],
                    [('sellPriceArgN, handling fee considered, from LOW to HIGH',
                      'sellTotalAmountN'), ]
                ),
            },
        }
    ) -> [
        (
            ('buyExchange: the exchange to sell assets',
            'sellExchange: the exchange to buy assets'),
            ('level',
            'amount'),
        ),
    ]:

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

def cbCondition(body1, body2):
    ob1 = json.loads(body1)
    ob2 = json.loads(body2)
    print(ob1['asks'][0], ob2['bids'][0])

@defer.inlineCallbacks
def cbNext():
    global count
    print('Loop:', count)
    count += 1
    # time.sleep(1)
    # d = task.deferLater(reactor, 0, main, reactor)
    try:
        bids1, asks1 = yield gateio.getOrderBook(('eth', 'usdt'))
        # print(len(bids1))
        bids2, asks2 = yield bitfinex.getOrderBook(('eth', 'usdt'))
        # print(len(bids2))
    except Exception as err:
        print(err)
    # print(len(bids1), len(bids2))
    try:
        exchangeState = dict()

        exchangeState['gateio'] = dict()
        exchangeState['bitfinex'] = dict()

        avgBids1 = calcMean(bids1)
        avgAsks1 = calcMean(asks1, True)

        # print(avgBids1)

        exchangeState['gateio']['actual'], exchangeState['gateio']['avg'] = [bids1, asks1], [avgBids1, avgAsks1]

        avgBids2 = calcMean(bids2)
        avgAsks2 = calcMean(asks2)

        # print(avgBids2)

        exchangeState['bitfinex']['actual'], exchangeState['bitfinex']['avg'] = [bids2, asks2], [avgBids2, avgAsks2]
    except Exception as err:
        print(err)

    exchangePairs = verifyExchanges(exchangeState)
    print(exchangePairs)


    yield cbNext()


reactor.callWhenRunning(cbNext)
reactor.run()
