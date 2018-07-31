from exchange import GetBuySell, GetOrder, Buy, Sell, FEE, GetBalance
import time

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

def run(exchanges, coinPair):
    while True:
        exchangeState = dict()
        for exchange in exchanges:
            exchangeState[exchange] = dict()
            # print(exchange)
            actual, avg = GetBuySell(exchange, coinPair)

            exchangeState[exchange]['actual'], exchangeState[exchange]['avg'] = actual, avg


        exchangePairs = verifyExchanges(exchangeState)
        print(exchangePairs)


        for exchangePair, pricePair, amountPair in exchangePairs[:1]:
            buyExName, sellExName = exchangePair
            buyPrice, sellPrice = pricePair
            level, amount = amountPair

            amount = 0.02
            coin, money = coinPair
            flag = True
            while flag:
                try:
                    coinAmount = GetBalance(buyExName, coin)
                    flag = False
                except:
                    flag = True

            flag = True
            while flag:
                try:
                    moneyAmount = GetBalance(sellExName, money)
                    flag = False
                except:
                    flag = True

            if coinAmount < amount:
                print(buyExName, coin, '数量不足')
                print(coinAmount)
                continue

            if moneyAmount < amount * sellPrice:
                print(sellExName, money, '数量不足')
                print(moneyAmount)
                continue

            try:
                buyOrderId = Buy(sellExName, coinPair, sellPrice, amount)
            except:
                continue
            try:
                sellOrderId = Sell(buyExName, coinPair, buyPrice, amount)
            except:
                continue

            buyOrder = None
            sellOrder = None

            while True:
                if not buyOrder or buyOrder.status != 'done':
                    buyOrder = GetOrder(sellExName, coinPair, buyOrderId)
                if not sellOrder or sellOrder.status != 'done':
                    sellOrder = GetOrder(buyExName, coinPair, sellOrderId)
                if buyOrder.status == 'done' and sellOrder.status == 'done':
                    break

            print(buyOrder)
            print(sellOrder)
            return None

if __name__ == "__main__":
    run(['gateio', 'bitfinex'], ('btc', 'usdt'))
    # print(GetBuySell('bitfinex', ('eth', 'usdt')))
