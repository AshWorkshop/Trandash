from exchange import *
import time

def verifyExchanges(
        exchangesData: {
            'exchangeName': (
                [('buyPriceArgN, handling fee considered, from HIGH to LOW',
                  'buyTotalAmountN'), ],
                [('sellPriceArgN, handling fee considered, from LOW to HIGH',
                  'sellTotalAmountN'), ]
            ),
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
        for sellExName, sellEx in exchangesData.items():
            if buyExName == sellExName: continue
            if buyEx[BUY][0][PRICE] < sellEx[SELL][0][PRICE]: continue

            level = 0
            amount = 0

            for i, (buy, sell) in enumerate(zip(buyEx[BUY], sellEx[SELL])):
                if buy[PRICE] < sell[PRICE]:
                    level = i - 1
                    amount = min(buyEx[BUY][level][AMOUNT], sellEx[SELL][level][AMOUNT])
                    break

            validExPairs.append( ((buyExName, sellExName), (level, amount)) )

    return validExPairs

def run(exchanges, coinPairs):
    while True:
        exchangeState = dict()
        for exchange in exchanges:
            buys, sells = GetBuySell(exchange, coinPair)
            total = 0
            totalAmount = 0
            buyAvg = []
            for price, amount in buys:
                total += price * amount
                totalAmount += amount
                buyAvg.append((total / totalAmount, totalAmount))

            total = 0
            totalAmount = 0
            sellAvg = []
            for price, amount in sells:
                total += price * amount
                totalAmount += amount
                sellAvg.append((total / totalAmount, totalAmount))
            exchangeState[exchange] = (buyAvg, sellAvg)

        exchangePairs = verifyExchanges(exchangeState)

if __name__ == "main":
    run(['huobi', 'gate', 'bitfinex'], ('eth', 'usdt'))
