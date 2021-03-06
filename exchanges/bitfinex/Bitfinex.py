from .BitfinexAPI import API
from utils import Order, calcMean, jsonToList
import json
from .bitfinex_key import ApiKey, SecretKey

## 填写 apiKey APISECRET
apiKey = ApiKey
secretKey = SecretKey
## address
btcAddress = 'your btc address'

# ## Provide constants

bitfinex = API(key=apiKey, secret_key=secretKey)

def toCoinPairStr(coinPair):
    coin, money = coinPair
    if money == 'usdt':
        money = 'usd'  #Bitfinex API的symbol列表中只有usd，无usdt
    coin_pair = ''.join((coin, money))

    return coin_pair

def GetBuySell(coinPair):
    data = bitfinex.orderbook(symbol=toCoinPairStr(coinPair))
    # print(data)
    asksj = data['asks']   #json列表
    bidsj = data['bids']   #json列表
    """
    asks和bids列表中的每一个元素都是json，eg:
    {
    "price":"574.62",
    "amount":"19.1334",
    "timestamp":"1472506126.0"
    }
    故将json列表转化为二维列表
    """
    asks = jsonToList(asksj)
    bids = jsonToList(bidsj)
    avgAsks = calcMean(asks)
    avgBids = calcMean(bids)
    return ((bids, asks), (avgBids, avgAsks))

def GetBalance(coin):
    balance = 0.0
    balance_list = bitfinex.wallet_balances()
    # print(balance_list)
    if coin == 'usdt':
        coin = 'usd'
    for b in balance_list:
        if b['type'] == 'exchange':
            if b['currency'] == coin:
                # print(b['currency'])
                balance = float(b['available'])  #balance that is available to trade
                break
    return balance

def Buy(coinPair, price, amount):
    data = bitfinex.new_order(
        symbol=toCoinPairStr(coinPair),
        amount=str(amount),
        price=str(price),
        side='buy',
        order_type='exchange limit'
    )
    # print(data)
    return int(data['order_id'])

def Sell(coinPair, price, amount):
    data = bitfinex.new_order(
        symbol=toCoinPairStr(coinPair),
        amount=str(amount),
        price=str(price),
        side='sell',
        order_type='exchange limit'
    )
    # print(data)
    return int(data['order_id'])

def GetOrder(coinPair, orderId):
    data = bitfinex.order_status(
        order_id=orderId
    )
    status = 'open'
    if data['is_cancelled']:
        status = 'cancelled'
    elif not data['is_live']:      #若没有被取消，并且不能继续被填充（not live），
        status = 'done'            #则表示交易已完成（done）
    # print(data)
    return Order(
        'bitfinex',
        orderId,
        data['side'],
        float(data['price']),
        float(data['original_amount']),
        coinPair,
        status
    )

def symbols():
    data = bitfinex.symbols()
    # print(data)
    return data

symbolsList = bitfinex.symbols()
usdDistrict = []
for symbol in symbolsList:
    # print(symbol[3:])
    if symbol[3:] == 'usd':
        usdDistrict.append(symbol)
print('usdDistrict:')
print(usdDistrict)
# otherDistrict = dict()
# for symbol in symbolsList:
#     for symbolu in usdDistrict:
#         if symbolu[:3] == symbol[3:]:
#             otherDistrict[symbol[3:]] = symbol
# print('otherDistrict:')
# print(otherDistrict)
hasList = []  #符合：“同时为usd区的货币的两个币的组合，这个组合在整个bitfinex的交易对里”
for symbol in usdDistrict:
    for symbolo in usdDistrict:
        symbolm = ''.join((symbol[:3],symbolo[:3]))
        if symbolm in symbolsList and symbolm not in hasList:
            hasList.append(symbolm)
# hasList = list(set(hasList))           
print('hasList:')
print(len(hasList),hasList)
midList = []  #可作为中间货币的列表
for symbol in hasList:
    midList.append(symbol[3:])
midList = list(set(midList))
print('midList:')
print(midList)