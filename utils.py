import six
import math

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

    def __str__(self):
        return str({
            'orderId': self.orderId,
            'type': self.type,
            'iniPrice': self.initPrice,
            'initAmount': self.initAmount,
            'coinPair': self.coinPair,
            'status': self.status,
            'exchange': self.exchange
        })

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


def getLevel(amount, dataList):
    """
    用于根据给定市场深度信息（买/卖单方面的[price,amount]列表），
    计算出为了吃掉给定数量，所需的深度level
    """
    remainAmount = amount
    AMOUNT = 1
    level = 0
    for bData in dataList:
        if remainAmount <= dataList[level][AMOUNT]:
            break
        else:
            remainAmount -= dataList[level][AMOUNT]
            level += 1
    return level


def to_bytes(text, encoding=None, errors='strict'):
    """Return the binary representation of `text`. If `text`
    is already a bytes object, return it as-is."""
    if isinstance(text, bytes):
        return text
    if not isinstance(text, six.string_types):
        raise TypeError('to_bytes must receive a unicode, str or bytes '
                        'object, got %s' % type(text).__name__)
    if encoding is None:
        encoding = 'utf-8'
    return text.encode(encoding, errors)


def calcMA(KLines):
    result = 0
    timestamp = KLines[-1][0]
    # print(len(KLines))
    for KLine in KLines:
        _, _, _, _, close, _, _ = KLine
        result += close
    return (timestamp, result / len(KLines))

def calcMAs(KLines, ma=200):
    result = []
    for i in range(ma - 1, len(KLines)):
        result.append(calcMA(KLines[i - ma + 1: i + 1]))

    return result

def calcBoll(KLines):
    result = 0
    timestamp = KLines[-1][0]
    # print(timestamp)
    N = len(KLines)
    for KLine in KLines:
        _, _, _, _, close, _, _ = KLine
        result += close
    mid = result / N

    result = 0
    for KLine in KLines:
        _, _, _, _, close, _, _ = KLine
        result += (close - mid) ** 2
    sigma = math.sqrt(result / N)

    up = mid + 2 * sigma
    down = mid - 2 * sigma
    
    return (timestamp, up, mid, down)

def calcBolls(KLines, ma=20):
    result = []
    for i in range(ma - 1, len(KLines)):
        result.append(calcBoll(KLines[i - ma + 1: i + 1]))
    return result
        
