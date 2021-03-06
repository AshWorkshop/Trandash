from twisted.logger import Logger
import six
import math
import time
from operator import itemgetter

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
    log = Logger('getLevel')
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
    log.debug('getLevel:\n{level}', level=level)
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
    # log = Logger('calcMA')
    result = 0
    timestamp = KLines[-1][0]
    # log.debug("{length}", length=len(KLines))
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
    # log = Logger('calcBoll')
    result = 0
    timestamp = KLines[-1][0]
    # log.debug("{timestamp}", timestamp=timestamp)
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
    #orderBook: one of bids or asks (type: list) ps:including orderId, sorted required
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
            orderIdList.append([orderBook[level][ORDERID], level])  #including each index in origin list
            count = level
            while count+1 < lenth and orderBook[count][PRICE] == orderBook[count+1][PRICE]:
                amount += orderBook[count+1][AMOUNT]
                orderIdList.append([orderBook[count+1][ORDERID], count+1])
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
      'cancel':[1357684 (# orderId), 1357898, ...]}
    """
    log = Logger('adjustOrderBook')
    adjustmentDict = dict()
    adjustmentDict['bids'] = list()
    adjustmentDict['asks'] = list()
    adjustmentDict['cancel'] = list()
    nBids = newState['orderbooks']['bids']
    nAsks = newState['orderbooks']['asks']
    oBids = newState['sisty']['orderbook']['bids']  #including orderId in each level
    oAsks = newState['sisty']['orderbook']['asks']  #including orderId in each level
    log.debug("oBids:\n{oBids}", oBids=oBids)
    oBids = sorted(oBids, key=itemgetter(0,1), reverse=True)  #sort: price from high to low; amount from low to high
    log.debug("sorted_oBids:\n{oBids}", oBids=oBids)
    oAsks = sorted(oAsks, key=itemgetter(0,1))  #sort: price from low to high; amount from low to high
    mergedBids = mergeOrderBook(oBids, capacity=capacity)  #including orderIdList in each level
    mergedAsks = mergeOrderBook(oAsks, capacity=capacity)  #including orderIdList in each level
    log.debug("mergedBids:\n{mergedBids}", mergedBids=mergedBids)
    log.debug("mergedAsks:\n{mergedAsks}", mergedAsks=mergedAsks)
    notCuttedBids = list()
    notCuttedAsks = list()
    cancelBidsList = list()  #including an oringin index list of each cancel level
    cancelAsksList = list()  #including an oringin index list of each cancel level

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
                cancelBidsList.append([nBids[n][PRICE], deltaAmount, mergedBids[oIndex][ORDERID]])
    """
    3.若n中无 o中有 的价格，则把全部价格等于此价格的单撤掉。
    """
    for o in range(len(mergedBids)):
        if oBidPrices[o] not in nBidPrices:
            cancelBidsList.append([mergedBids[o][PRICE], mergedBids[o][AMOUNT], mergedBids[o][ORDERID]])

    """
    处理撤单
    DONE: sort cancelBidsList to let it: price from high to low
    """
    log.debug("cancelBidsList:\n{cancelBidsList}", cancelBidsList=cancelBidsList)
    sortedCancelBids = sorted(cancelBidsList, key=itemgetter(0,1), reverse=True) 
    log.debug("sortedCancelBids:\n{sortedCancelBids}", sortedCancelBids=sortedCancelBids)

    for i in range(len(sortedCancelBids)):
        decimal = sortedCancelBids[i][AMOUNT] % capacity
        remainAmount = sortedCancelBids[i][AMOUNT]
        log.debug("remainAmount:\n{remainAmount}", remainAmount=remainAmount)
        if decimal == 0:
            oBids = sorted(oBids, key=itemgetter(1), reverse=True)
            oBids = sorted(oBids, key=itemgetter(0), reverse=True)
            """
            DONE: sort oBids to let it:
            1.price from high to low
            2.amount from high to low
            """
        else:
            oBids = oBids
            """
            DONE: sort oBids to let it:
            1.price from high to low
            2.amount from low to high
            """
        for j in range(len(oBids)):
            if oBids[j][PRICE] == sortedCancelBids[i][PRICE]:
                log.debug("inner remainAmount:\n{remainAmount}", remainAmount=remainAmount)
                if remainAmount > 0:
                    orderId = oBids[j][ORDERID]
                    adjustmentDict['cancel'].append(orderId)
                    remainAmount -= oBids[j][AMOUNT]
                elif remainAmount == 0:
                    
                    break
                elif remainAmount < 0 and abs(remainAmount) <= capacity:
                    adjustmentDict['bids'].append([oBids[j][PRICE], abs(remainAmount)])
                    
                    break
                else:
                    raise("handle sortedCancelBids error")
    log.debug("notCuttedBids inner:\n{notCuttedBids}", notCuttedBids=notCuttedBids)
    cuttedBids = cutOrderBook(notCuttedBids, capacity=capacity)
    log.debug("cuttedBids inner:\n{cuttedBids}", cuttedBids=cuttedBids)
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
                cancelAsksList.append([nAsks[n][PRICE], deltaAmount, mergedAsks[oIndex][ORDERID]])
    """
    3.若n中无 o中有 的价格，则把全部价格等于此价格的单撤掉。
    """
    for o in range(len(mergedAsks)):
        if oAskPrices[o] not in nAskPrices:
            cancelAsksList.append([mergedAsks[o][PRICE], mergedAsks[o][AMOUNT], mergedAsks[o][ORDERID]])

    """
    处理撤单
    DONE: sort cancelAsksList to let it: price from low to high
    """
    log.debug("cancelAsksList:\n{cancelAsksList}", cancelAsksList=cancelAsksList)
    sortedCancelAsks = sorted(cancelAsksList, key=itemgetter(0,1)) 
    log.debug("sortedCancelAsks:\n{sortedCancelAsks}", sortedCancelAsks=sortedCancelAsks)    
    for i in range(len(sortedCancelAsks)):
        decimal = sortedCancelAsks[i][AMOUNT] % capacity
        remainAmount = sortedCancelAsks[i][AMOUNT]
        log.debug("remainAmount:\n{remainAmount}", remainAmount=remainAmount)
        if decimal == 0:
            oAsks = sorted(oAsks, key=itemgetter(1), reverse=True)
            oAsks = sorted(oAsks, key=itemgetter(0))
            log.debug("decimal == 0 oAsks:\n{oAsks}", oAsks=oAsks) 
            """
            DONE: sort oAsks to let it:
            1.price from low to high
            2.amount from high to low
            """
        else:
            oAsks = oAsks
            log.debug("decimal != 0 oAsks:\n{oAsks}", oAsks=oAsks) 
            """
            DONE: sort oAsks to let it:
            1.price from low to high
            2.amount from low to high
            """
        for j in range(len(oAsks)):
            if oAsks[j][PRICE] == sortedCancelAsks[i][PRICE]:
                log.debug("inner remainAmount:\n{remainAmount}", remainAmount=remainAmount)
                if remainAmount > 0:
                    orderId = oAsks[j][ORDERID]
                    adjustmentDict['cancel'].append(orderId)
                    remainAmount -= oAsks[j][AMOUNT]
                elif remainAmount == 0:
                    
                    break
                elif remainAmount < 0 and abs(remainAmount) <= capacity:
                    adjustmentDict['asks'].append([oAsks[j][PRICE], abs(remainAmount)])
                    
                    break
                else:
                    raise("handle sortedCancelAsks error")

    log.debug("notCuttedAsks inner:\n{notCuttedAsks}", notCuttedAsks=notCuttedAsks)
    log.debug("sortedCancelAsks inner:\n{sortedCancelAsks}", sortedCancelAsks=sortedCancelAsks)
    cuttedAsks = cutOrderBook(notCuttedAsks, capacity=capacity)
    adjustmentDict['asks'].extend(cuttedAsks)

    return adjustmentDict

def commitOrderBook(newState,exchange):
    BIDS,ASKS = range(2)
    PRICE,AMOUNT,EXCHANGE = range(3)
    POWER = [0.5,0.5]

    newState['orderbooks'] = {'bids':[],'asks':[],"time":0}
    A,B = 0,0
    maxLevelA = len(newState[exchange[0]]['orderbook'][BIDS])
    maxLevelB = len(newState[exchange[1]]['orderbook'][BIDS])
    while A < maxLevelA and B < maxLevelB:
        orderA = newState[exchange[0]]['orderbook'][BIDS][A]
        orderB = newState[exchange[1]]['orderbook'][BIDS][B]
        if orderA[PRICE] == orderB[PRICE]:
            orderA[AMOUNT] = orderA[AMOUNT]*POWER[0] + orderB[AMOUNT]*POWER[1]
            newState['orderbooks']['bids'].append(orderA)
            A += 1
            B += 1
        elif orderA[PRICE] > orderB[PRICE]:
            newState['orderbooks']['bids'].append(orderA)
            A += 1
        else:
            newState['orderbooks']['bids'].append(orderB)
            B += 1
    if maxLevelA >= maxLevelB:
        while A < maxLevelA:
            orderA = newState[exchange[0]]['orderbook'][BIDS][A]
            newState['orderbooks']['bids'].append(orderA)
            A += 1
    elif maxLevelA < maxLevelB:
        while B < maxLevelB:
            orderB = newState[exchange[1]]['orderbook'][BIDS][B]
            newState['orderbooks']['bids'].append(orderB)
            B += 1

    A,B = 0,0
    maxLevelA = len(newState[exchange[0]]['orderbook'][ASKS])
    maxLevelB = len(newState[exchange[1]]['orderbook'][ASKS])
    while A < maxLevelA and B < maxLevelB:
        orderA = newState[exchange[0]]['orderbook'][ASKS][A]
        orderB = newState[exchange[1]]['orderbook'][ASKS][B]
        if orderA[PRICE] == orderB[PRICE]:
            orderA[AMOUNT] = orderA[AMOUNT]*POWER[0] + orderB[AMOUNT]*POWER[1]
            newState['orderbooks']['asks'].append(orderA)
            A += 1
            B += 1
        elif orderA[PRICE] < orderB[PRICE]:
            newState['orderbooks']['asks'].append(orderA)
            A += 1
        else:
            newState['orderbooks']['asks'].append(orderB)
            B += 1
    if maxLevelA >= maxLevelB:
        while A < maxLevelA:
            orderA = newState[exchange[0]]['orderbook'][BIDS][A]
            newState['orderbooks']['asks'].append(orderA)
            A += 1
    elif maxLevelA < maxLevelB:
        while B < maxLevelB:
            orderB = newState[exchange[1]]['orderbook'][BIDS][B]
            newState['orderbooks']['asks'].append(orderB)
            B += 1

    newState['orderbooks']['time'] = time.time()
    return newState
