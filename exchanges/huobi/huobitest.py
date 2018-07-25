from HuobiAPI import *
from utils import calcMean,Order



def toCoinPairStr(coinPair):
    return (''.join(coinPair))

def toGradeStr(grade):
    return ('step'+str(grade))

def GetBuySell(coinPair,grade=0):
    depth = get_depth(toCoinPairStr(coinPair),toGradeStr(grade))
    asks = depth['tick']['asks']  #卖单
    bids = depth['tick']['bids']  #买单
    asks = calcMean(asks)
    bids = calcMean(bids)
    #print('卖单',asks)
    #print('买单',bids)
    return (asks,bids)

def GetBalance(coin):
    coin = 'eth'
    restant = {}
    balance = get_balance()['data']['list']
    for b in balance:
        if b['currency'] == coin:
            if b['type'] == 'trade':
                restant['trade'] = b['balance']
            elif b['type'] == 'frozen':
                restant['frozen'] = b['balance']
    return restant

def Sell(coinPair, price, amount):
#    {amount: "0.001", price: "466.10", type: "sell-limit", source: "web", symbol: "ethusdt",…}
    data = send_order(amount=amount, source="web", symbol=toCoinPairStr(coinPair), _type="sell-limit", price=price)
    print(data)
    return int(order['data'])

def Buy(coinPair,price,amount):
    data = send_order(amount = amount,source = "web",symbol=toCoinPairStr(coinPair), _type="buy-limit", price=price)
    print(data)
    return int(order['data'])

def GetOrder(coinPair, orderId):
    data = order_info(orderId)
    if data['data']['type']=='buy-limit':
        data['data']['type']='buy'
    elif data['data']['type']=='sell-limit':
        data['data']['type']='sell'
    print(data)
    return Order(
        'huobi',
        orderId,
        data['data']['type'],
        float(data['data']['price']),
        float(data['data']['amount']),
        coinPair,
        data['order']['status'],
    )
