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
    print('getLevel:')
    print(level)
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


PRICE, AMOUNT, ORDERID = range(3)        
def cutOrderBook(orderBook, capacity=100, hasID=False):
    #orderBook: one of bids or asks (type: list)
    #return: cuttedOrderBook, also one of  bids or asks (list of: [price1, capacity],...,[priceN, remainAmount])
    cuttedOrderBook = list()

    for data in orderBook:
        remainAmount = data[AMOUNT]
        while remainAmount >= capacity:
            remainAmount -= capacity
            if hasID:
                cuttedOrderBook.append([data[PRICE], capacity, data[ORDERID]])
            else:
                cuttedOrderBook.append([data[PRICE], capacity])
        if remainAmount != 0:
            if hasID:
                cuttedOrderBook.append([data[PRICE], remainAmount, data[ORDERID]])
            else:
                cuttedOrderBook.append([data[PRICE], remainAmount])

    return cuttedOrderBook

def mergeOrderBook(orderBook, capacity=100, hasID=True):
    #orderBook: one of bids or asks (type: list) ps:including orderId
    #return: mergedOrderBook, also one of  bids or asks 
    #return: list of: [price1, amount1, [orderIdList1]],...,[priceN, amountN, [orderIdListN]]
    mergedOrderBook = list()
    
    level = 0
    count = 0
    lenth = len(orderBook)
    while level < lenth:
        amount = orderBook[level][AMOUNT]
        if hasID:
            orderIdList = list()
            orderIdList.append(orderBook[level][ORDERID])
            count = level
            while count+1 < lenth and orderBook[count][PRICE] == orderBook[count+1][PRICE]:
                amount += orderBook[count+1][AMOUNT]
                orderIdList.append(orderBook[count+1][ORDERID])
                count += 1
            mergedOrderBook.append([orderBook[count][PRICE], amount, orderIdList])
            level = count+1
        else:
            count = level
            while count+1 < lenth and orderBook[count][PRICE] == orderBook[count+1][PRICE]:
                amount += orderBook[count+1][AMOUNT]
                count += 1
            mergedOrderBook.append([orderBook[count][PRICE], amount])
            level = count+1            

    return mergedOrderBook

def adjustOrderBook(newState, capacity=100):
    """    
    思路2：将old深度表合并成“价格唯一，数量求和”的合并表，(用mergeOrderBook()函数)
    直接拿这份表和目标深度n表对比，比较价格：
    1.若n中有o中没有的价格，则以相应数量和价格挂单；
    2.若n中有o中有的价格，则比较o总量和n总量，以差量挂撤；
    3.若n中无o中有的价格，则把全部价格等于此价格的单撤掉。
    return: adjustmentDict ; eg:
    { 'bids': [[276, 1], [276, 1], [274, 1], [274, 1], [274,1], ....], 
      'asks':[[278, 1], [278, 0.5], ...], 
      'cancle':[1357684 (# orderId), 1357898, ...]}
    """
    adjustmentDict = dict()
    adjustmentDict['bids'] = list()
    adjustmentDict['asks'] = list()
    adjustmentDict['cancle'] = list()

    nBids = newState['orderbooks']['bids']
    nAsks = newState['orderbooks']['asks']
    oBids = newState['sisty']['orderbook']['bids']  #including orderId in each level
    oAsks = newState['sisty']['orderbook']['asks']  #including orderId in each level
    mergedBids = mergeOrderBook(oBids)  #including orderIdList in each level
    mergedAsks = mergeOrderBook(oAsks)  #including orderIdList in each level
    # print("mergedBids:")
    # print(mergedBids)
    # print("mergedAsks:")
    # print(mergedAsks)
    notCuttedBids = list()
    notCuttedAsks = list()
    cancleBidsList = list()
    cancleAsksList = list()

    """
    bids: price from high to low
    """
    oBidPrices = list()
    for oBid in mergedBids:
        oBidPrices.append(oBid[PRICE])
    nBidPrices = list()
    for nBid in nBids:
        nBidPrices.append(nBid[PRICE])    

    for n in range(len(nBids)):
        """
        1.若n中有 o中没有 的价格，则以相应数量和价格挂单；
        """
        if nBidPrices[n] not in oBidPrices:
            notCuttedBids.append([nBids[n][PRICE], nBids[n][AMOUNT]])
        """
        2.若n中有 o中有 的价格，则比较o总量和n总量，以差量挂撤；
        """
        if nBidPrices[n] in oBidPrices:
            oIndex = oBidPrices.index(nBidPrices[n])
            if nBids[n][AMOUNT] > mergedBids[oIndex][AMOUNT]:
                deltaAmount = nBids[n][AMOUNT] - mergedBids[oIndex][AMOUNT]
                notCuttedBids.append([nBids[n][PRICE], deltaAmount])
            elif nBids[n][AMOUNT] < mergedBids[oIndex][AMOUNT]:
                deltaAmount = mergedBids[oIndex][AMOUNT] - nBids[n][AMOUNT]
                cancleBidsList.append([nBids[n][PRICE], deltaAmount])
    """
    3.若n中无 o中有 的价格，则把全部价格等于此价格的单撤掉。
    """            
    for o in range(len(mergedBids)):
        if oBidPrices[o] not in nBidPrices:
            cancleBidsList.append([mergedBids[o][PRICE], mergedBids[o][AMOUNT]])
   
    """
    处理撤单
    TO DO: sort cancleBidsList to let it: price from high to low
    """ 
    # mini = 0
    for i in range(len(cancleBidsList)):
        decimal = cancleBidsList[i][AMOUNT] % capacity
        remainAmount = cancleBidsList[i][AMOUNT]
        # print("remainAmount:")
        # print(remainAmount)
        if decimal == 0:
            oBids = oBids 
            """            
            TO DO: sort oBids to let it:
            1.price from high to low
            2.amount from high to low
            """
        else: 
            oBids = oBids 
            """            
            TO DO: sort oBids to let it:
            1.price from high to low
            2.amount from low to high
            """
        for j in range(len(oBids)):
            if oBids[j][PRICE] == cancleBidsList[i][PRICE]:
                # print("inner remainAmount:")
                # print(remainAmount)
                if remainAmount > 0:
                    orderId = oBids[j][ORDERID] 
                    adjustmentDict['cancle'].append(orderId)
                    remainAmount -= oBids[j][AMOUNT]
                elif remainAmount == 0:
                    # mini = j
                    break
                elif remainAmount < 0 and abs(remainAmount) <= capacity:
                    adjustmentDict['bids'].append([oBids[j][PRICE], abs(remainAmount)])
                    # mini = j
                    break
                else:
                    raise("handle cancleBidsList error")
    # print("notCuttedBids inner:")
    # print(notCuttedBids)
    # print("cancleBidsList inner:")
    # print(cancleBidsList)
    cuttedBids = cutOrderBook(notCuttedBids)
    adjustmentDict['bids'].extend(cuttedBids)

    """ 
    asks: price from low to high
    """
    oAskPrices = list()
    for oAsk in mergedAsks:
        oAskPrices.append(oAsk[PRICE])
    nAskPrices = list()
    for nAsk in nAsks:
        nAskPrices.append(nAsk[PRICE])

    for n in range(len(nAsks)):
        """
        1.若n中有 o中没有 的价格，则以相应数量和价格挂单；
        """
        if nAskPrices[n] not in oAskPrices:
            notCuttedAsks.append([nAsks[n][PRICE], nAsks[n][AMOUNT]])
        """
        2.若n中有 o中有 的价格，则比较o总量和n总量，以差量挂撤；
        """
        if nAskPrices[n] in oAskPrices:
            oIndex = oAskPrices.index(nAskPrices[n])
            if nAsks[n][AMOUNT] > mergedAsks[oIndex][AMOUNT]:
                deltaAmount = nAsks[n][AMOUNT] - mergedAsks[oIndex][AMOUNT]
                notCuttedAsks.append([nAsks[n][PRICE], deltaAmount])
            elif nAsks[n][AMOUNT] < mergedAsks[oIndex][AMOUNT]:
                deltaAmount = mergedAsks[oIndex][AMOUNT] - nAsks[n][AMOUNT]
                cancleAsksList.append([nAsks[n][PRICE], deltaAmount])
    """
    3.若n中无 o中有 的价格，则把全部价格等于此价格的单撤掉。
    """            
    for o in range(len(mergedAsks)):
        if oAskPrices[o] not in nAskPrices:
            cancleAsksList.append([mergedAsks[o][PRICE], mergedAsks[o][AMOUNT]])
   
    """
    处理撤单
    TO DO: sort cancleAsksList to let it: price from low to high
    """ 
    # mini = 0
    for i in range(len(cancleAsksList)):
        decimal = cancleAsksList[i][AMOUNT] % capacity
        remainAmount = cancleAsksList[i][AMOUNT]
        print("remainAmount:")
        print(remainAmount)
        if decimal == 0:
            oAsks = oAsks 
            """            
            TO DO: sort oAsks to let it:
            1.price from low to high
            2.amount from high to low
            """
        else: 
            oAsks = oAsks 
            """            
            TO DO: sort oAsks to let it:
            1.price from low to high
            2.amount from low to high
            """
        for j in range(len(oAsks)):            
            if oAsks[j][PRICE] == cancleAsksList[i][PRICE]:
                print("inner remainAmount:")
                print(remainAmount)                
                if remainAmount > 0:
                    orderId = oAsks[j][ORDERID] 
                    adjustmentDict['cancle'].append(orderId)
                    remainAmount -= oAsks[j][AMOUNT]
                elif remainAmount == 0:
                    # mini = j
                    break
                elif remainAmount < 0 and abs(remainAmount) <= capacity:
                    adjustmentDict['asks'].append([oAsks[j][PRICE], abs(remainAmount)])
                    # mini = j
                    break
                else:
                    raise("handle cancleBidsList error")

    # print("notCuttedAsks inner:")
    # print(notCuttedAsks)
    # print("cancleAsksList inner:")
    # print(cancleAsksList)
    cuttedAsks = cutOrderBook(notCuttedAsks)
    adjustmentDict['asks'].extend(cuttedAsks)

    return adjustmentDict