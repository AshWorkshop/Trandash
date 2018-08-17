from twisted.internet import defer, task
from twisted.internet import reactor
from twisted.python.failure import Failure
from exchanges.bitfinex.BitfinexService import bitfinex
import time
from sys import argv


from cycle.cycle import Cycle
from robots.robot import Robot
from utils import calcMAs, calcBolls

def getAvg(things):
    total = 0
    totalAmount = 0
    for price, amount in things:
        amount = amount
        total += price * amount
        totalAmount += amount
    if totalAmount == 0:
        return (0.0, 0.0)
    return (total / totalAmount, totalAmount)

if len(argv) == 5:
    _, mode, coin, money, dataFile = argv
else:
    print("ERROR!")
    quit()

if money == 'usdt':
    money = 'usd'

pairs = (coin, money)

class BitfinexRobot(Robot):

    def init(self):
        self.data['buys'] = []
        self.data['sells'] = []
        self.data['buyp'] = None
        self.data['sellp'] = None
        self.data['mode'] = mode
        self.data['coin'] = coin
        self.data['money'] = money
        self.data['initBuyAmount'] = 0.0
        self.data['initSellAmount'] = 0.0
        self.data['pairs'] = pairs
        self.data['minAmount'] = 0.04
        self.data['rate'] = 0.006
        self.data['delta'] = 0.005
        self.data['amountRate'] = 1.618

        self.state = 'run'

    @defer.inlineCallbacks
    def buy(self, price, amount):
        orderId = 0
        try:
            _, orderId = yield bitfinex.buy(self.data['pairs'], price, amount)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())
        else:
            if orderId != 0:
                print('SUCCESSFULLY BUY:', orderId)

        self.data['buys'].append((price, amount))

        self.state = 'run'

    @defer.inlineCallbacks
    def sell(self, price, amount):
        orderId = 0
        try:
            _, orderId = yield bitfinex.sell(self.data['pairs'], price, amount)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())
        else:
            if orderId != 0:
                print('SUCCESSFULLY SELL:', orderId)

        self.data['sells'].append((price, amount))
        self.state = 'run'

    @defer.inlineCallbacks
    def buyp(self, price, amount):
        orderId = None
        cancel = False
        try:
            _, orderId = yield bitfinex.sell(self.data['pairs'], price, amount)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())
        else:
            if orderId is not None:
                print('SUCCESSFULLY BUYP:', orderId)
                try:
                    order = yield bitfinex.getOrder(self.data['pairs'], orderId)
                except Exception as err:
                    failure = Failure(err)
                    print(failure.getBriefTraceback())
                    cancel = True
                else:
                    if order.status != 'done':
                        cancel = True

        if cancel:
            self.state = 'wait'
            self.reactor.callWhenRunning(self.cancel, orderId)
        else:
            self.data['buyp'] = orderId
            self.data['buys'] = []
            self.state = 'run'

    @defer.inlineCallbacks
    def sellp(self, price, amount):
        orderId = None
        cancel = False
        try:
            _, orderId = yield bitfinex.buy(self.data['pairs'], price, amount)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())
        else:
            if orderId is not None:
                print('SUCCESSFULLY SELLP:', orderId)
                try:
                    order = yield bitfinex.getOrder(self.data['pairs'], orderId)
                except Exception as err:
                    failure = Failure(err)
                    print(failure.getBriefTraceback())
                    cancel = True
                else:
                    if order.status != 'done':
                        cancel = True

        if cancel:
            self.state = 'wait'
            self.reactor.callWhenRunning(self.cancel, orderId)
        else:
            self.data['sellp'] = orderId
            self.data['sells'] = []
            self.state = 'run'

    @defer.inlineCallbacks
    def cancel(self, orderId):
        try:
            result, data = yield bitfinex.cancel(self.data['pairs'], orderId)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())
        else:
            if result:
                print('SUCCESSFULLY CANCEL:', orderId)

        self.state = 'run'




    def run(self):
        cycleData = self.data['cycleData']
        KLines = cycleData['klines']
        ticker = cycleData['ticker']
        balances = cycleData['balances']
        catch = False



        if not catch and KLines is not None and ticker is not None and balances is not None:
            buys = self.data['buys'] # 已成交的买单，相当于开多单
            sells = self.data['sells'] # 已成交的卖单，相当于开空单
            print('balances:', balances)
            MAs = calcMAs(KLines, ma=30)
            _, ma = MAs[-1]
            buy1 = ticker[0]
            sell1 = ticker[2]
            last_price = ticker[-4]
            print('buy1 && sell1:', buy1, sell1)
            print('last_price && ma:', last_price, ma)
            if last_price > ma and len(self.data['buys']) == 0 and self.data['mode'] == 'buy':
                print('BUY')
                initBuyAmount = self.data['initBuyAmount'] = balances.get(self.data['money'], 0.0) / last_price * 0.001
                if initBuyAmount > 0 and initBuyAmount < self.data['minAmount'] and (balances.get(self.data['money'], 0.0) / sell1) >= self.data['minAmount']:
                    initBuyAmount = self.data['initBuyAmount'] = self.data['minAmount']

                print('initBuyAmount', self.data['initBuyAmount'])
                if initBuyAmount >= 0.04:
                    self.data['delta'] = 0.005
                    self.state = 'wait'
                    catch = True
                    self.reactor.callWhenRunning(self.buy, sell1, initBuyAmount)
            elif last_price < ma and len(self.data['sells']) == 0 and self.data['mode'] == 'sell':
                print('SELL')
                initSellAmount = self.data['initSellAmount'] = balances.get(self.data['coin'], 0.0) * 0.001
                if initSellAmount > 0 and initSellAmount < self.data['minAmount'] and balances.get(self.data['coin'], 0.0) >= self.data['minAmount']:
                    initSellAmount = self.data['initSellAmount'] = self.data['minAmount']
                print('initSellAmount', self.data['initSellAmount'])
                if initSellAmount >= 0.04:
                    self.data['delta'] = 0.005
                    self.state = 'wait'
                    catch = True
                    self.reactor.callWhenRunning(self.sell, buy1, initSellAmount)



        if not catch and KLines is not None and ticker is not None and balances is not None:
            Bolls = calcBolls(KLines)
            klines = KLines[-3:]
            bolls = Bolls[-3:]
            llk, lk, k = klines
            llb, lb, b = bolls
            _, _, _, _, llk_close, _, _ = llk
            _, _, _, _, lk_close, _, _ = lk
            _, llb_u, _, llb_d = llb
            _, lb_u, _, lb_d = lb
            _, b_u, _, b_d = b
            buy1 = ticker[0]
            sell1 = ticker[2]
            last_price = ticker[-4]

            if self.data['mode'] == 'buy' and llk_close > llb_d and lk_close < lb_d:
                print('BUYBOLL')
                if len(self.data['buys']) > 0:
                    price, amount = self.data['buys'][-1]
                    if (price - last_price) / price > self.data['delta']:
                        if amount * self.data['amountRate'] < self.data['initBuyAmount'] * self.data['amountRate'] ** 6:
                            newAmount = amount * self.data['amountRate']
                        else:
                            newAmount = amount
                        if newAmount <= balances.get(self.data['money'], 0.0):
                            print('BUY', newAmount)
                            self.data['delta'] = (price - last_price) / price
                            self.state = 'wait'
                            catch = True
                            self.reactor.callWhenRunning(self.buy, sell1, newAmount)


            elif self.data['mode'] == 'sell'and llk_close < llb_u and lk_close > lb_u:
                print('SELLBOLL')
                if len(self.data['sells']) > 0:
                    price, amount = self.data['sells'][-1]
                    if (last_price - price) / price > self.data['delta']:
                        if amount * self.data['amountRate'] < self.data['initSellAmount'] * self.data['amountRate'] ** 6:
                            newAmount = amount * self.data['amountRate']
                        else:
                            newAmount = amount
                        if newAmount <= balances.get(self.data['coin'], 0.0):
                            print('SELL', newAmount)
                            self.data['delta'] = (last_price - price) / price
                            self.state = 'wait'
                            catch = True
                            self.reactor.callWhenRunning(self.sell, buy1, newAmount)




        # 平仓
        if not catch and ticker is not None:
            buy1 = ticker[0]
            sell1 = ticker[2]
            last_price = ticker[-4]
            if self.data['mode'] == 'buy' and len(self.data['buys']) > 0:
                avgPrice, totalAmount = getAvg(self.data['buys'])

                if (sell1 - avgPrice) / avgPrice > self.data['rate']:
                    self.state = 'wait'
                    catch = True
                    print('BUYP')
                    self.reactor.callWhenRunning(self.buyp, sell1, totalAmount)

            if self.data['mode'] == 'sell' and len(self.data['sells']) > 0:

                avgPrice, totalAmount = getAvg(self.data['sells'])

                if (avgPrice - buy1) / avgPrice > self.data['rate']:
                    self.state = 'wait'
                    catch = True
                    print('SELLP')
                    self.reactor.callWhenRunning(self.sellp, sell1, totalAmount)



    def wait(self):
        print('wait...')




klinesCycle = Cycle(reactor, bitfinex.getKLineLastMin, 'klines', limit=1, wait=50, clean=False)
klinesCycle.start(pairs, last=30)
tickerCycle = Cycle(reactor, bitfinex.getTicker, 'ticker', limit=1, wait=3, clean=False)
tickerCycle.start(pairs)
balancesCycle = Cycle(reactor, bitfinex.getBalances, 'balances', limit=1, wait=3)
balancesCycle.start(list(pairs))

states = ['init', 'run', 'wait']

bitfinexRobot = BitfinexRobot(reactor, states, [klinesCycle, tickerCycle, balancesCycle])
bitfinexRobot.start('init')
