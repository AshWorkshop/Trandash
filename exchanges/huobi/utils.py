class Order:
    orderId = 0
    initPrice = 0
    initAmount = 0
    coinPair = ('eth', 'usdt')
    status = 'open'
    exchange = None
    type = 'sell'

    def __init__(self, exchange, orderId, type, initPrice, initAmount, coinPair, status):
        self.orderId = orderId
        self.initPrice = initPrice
        self.initAmount = initAmount
        self.coinPair = coinPair
        self.status = status
        self.type = type
        self.exchange = exchange

def calcMean(dataList, reverse=False):
    total = 0
    totalAmount = 0
    result = []
    if reverse:
        dataList.reverse()
    for price, amount in dataList:
        total += float(price) * float(amount)
        totalAmount += float(amount)
        result.append((total / totalAmount, totalAmount))
    return result
