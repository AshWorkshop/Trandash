import exchanges.gateio.Gateio as gateio
import exchanges.huobi.Huobipro as huobipro
import exchanges.bitfinex.Bitfinex as bitfinex

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

def GetBuySell(exchange, coinPair):
    return EXCHANGE[exchange].GetBuySell(coinPair)

def GetBalance(exchange, coin):
    return EXCHANGE[exchange].GetBalance(coin)

def Buy(exchange, coinPair, price, amount):
    return EXCHANGE[exchange].Buy(coinPair, price, amount)

def Sell(exchange, coinPair, price, amount):
    return EXCHANGE[exchange].Sell(coinPair, price, amount)

def GetOrder(exchange, coinPair, orderId):
    return EXCHANGE[exchange].GetOrder(coinPair, orderId)
