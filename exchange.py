class Order:
    orderId = 0
    initPrice = 0
    initAmount = 0
    coinPaire = ('eth', 'usdt')
    state = 'panding'

def GetBuySell(exchange, coinPair):
    return ([], [])

def GetBalance(exchange, coin):
    return 0

def Buy(exchange, coinPair, price, amount):
    return 0

def Sell(exchange, coinPair, price, amount):
    return 0

def GetOrder(exchange, coinPair, orderId):
    return Order()
