import six

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

#用于将json列表转化为二维列表[[price, amount],...]的形式
def jsonToList(dataList):
    result_list = []
    for dic in dataList:
        price = float(dic['price'])
        amount = float(dic['amount'])
        result_list.append([price, amount])
    return result_list

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
    for KLine in KLines:
        timestamp, _, _, _, close, _, _ = KLine
        result += close
    return result / len(KLines)
