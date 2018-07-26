import exchanges.gateio.Gateio as gateio
import exchanges.huobi.Huobipro as huobipro

FEE = {
    'huobipro': [1.0, 1.0],
    'gateio': [1.0, 1.0],
}

EXCHANGE = {
    'huobipro': huobipro,
    'gateio': gateio
}

def GetBuySell(exchange, coinPair):
    return EXCHANGE[exchange].GetBuySell(coinPair)

def GetBalance(exchange, coin):
    return 0

def Buy(exchange, coinPair, price, amount):
    return 0

def Sell(exchange, coinPair, price, amount):
    return 0

def GetOrder(exchange, coinPair, orderId):
    return Order()
