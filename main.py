from exchange import *
import time

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
        # TODO: find two exhanges that can trade


if __name__ == "main":
    run(['huobi', 'gate', 'bitfinex'], ('eth', 'usdt'))
