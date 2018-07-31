from .gateAPI import GateIO
from utils import Order, calcMean
from .gateio_key import ApiKey, SecretKey
import json

## 填写 apiKey APISECRET
apiKey = ApiKey
secretKey = SecretKey
## address
btcAddress = 'your btc address'


## Provide constants

API_QUERY_URL = 'data.gateio.io'
API_TRADE_URL = 'api.gateio.io'

## Create a gate class instance

gate_query = GateIO(API_QUERY_URL, apiKey, secretKey)
gate_trade = GateIO(API_TRADE_URL, apiKey, secretKey)

def toCoinPairStr(coinPair):
    return '_'.join(coinPair)

def GetBuySell(coinPair):
    data = gate_query.orderBook(toCoinPairStr(coinPair))
    # print(data)
    asks = data['asks']
    bids = data['bids']
    avgAsks = calcMean(asks, True)
    avgBids = calcMean(bids)

    return ((bids, asks), (avgBids, avgAsks))

def GetBalance(coin):
    data = json.loads(gate_trade.balances())
    # print(data)
    return float(data['available'][coin.upper()])

def Buy(coinPair, price, amount):
    data = json.loads(gate_trade.buy(
        toCoinPairStr(coinPair),
        str(price),
        str(amount)
    ))
    # print(data)
    return int(data['orderNumber'])

def Sell(coinPair, price, amount):
    data = json.loads(gate_trade.sell(
        toCoinPairStr(coinPair),
        str(price),
        str(amount)
    ))
    # print(data)
    return int(data['orderNumber'])

def GetOrder(coinPair, orderId):
    data = json.loads(gate_trade.getOrder(
        str(orderId),
        toCoinPairStr(coinPair)
    ))
    print(data)
    status = data['order']['message']
    if status == 'Success':
        status = 'done'
    return Order(
        'gateio',
        orderId,
        data['order']['type'],
        float(data['order']['initialRate']),
        float(data['order']['initialAmount']),
        coinPair,
        status
    )
