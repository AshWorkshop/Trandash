from twisted.internet import defer, task
from twisted.internet import reactor
from twisted.python.failure import Failure
from exchanges.bitfinex.BitfinexService import bitfinex
import time
from sys import argv


from cycle.cycle import Cycle
from robots.robot import Robot
from utils import calcMAs, calcBolls

if len(argv) == 4:
    _, coin, money, dataFile = argv
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
        self.data['coin'] = coin
        self.data['money'] = money
        self.data['initBuyAmount'] = 0.0
        self.data['initSellAmount'] = 0.0
        self.data['pairs'] = pairs

        self.state = 'run'

    @defer.inlineCallbacks
    def buy(self, price, amount):
        try:
            orderId = yield bitfinex.buy(self.pairs, price, amount)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())
        else:
            if orderId != 0:
                print('SUCCESSFULLY BUY:', orderId)
                try:
                    order = yield bitfinex.getOrder(self.pairs, orderId)
                except Exception as err:
                    failure = Failure(err)
                    print(failure.getBriefTraceback())
                else:
                    self.data['buys'].append(order)

        self.state = 'run'

    @defer.inlineCallbacks
    def sell(self, price, amount):
        try:
            orderId = yield bitfinex.sell(self.pairs, price, amount)
        except Exception as err:
            failure = Failure(err)
            print(failure.getBriefTraceback())
        else:
            if orderId != 0:
                print('SUCCESSFULLY SELL:', orderId)
                try:
                    order = yield bitfinex.getOrder(self.pairs, orderId)
                except Exception as err:
                    failure = Failure(err)
                    print(failure.getBriefTraceback())
                else:
                    self.data['sells'].append(order)

        self.state = 'run'


    def run(self):
        cycleData = self.data['cycleData']
        KLines = cycleData['klines']
        ticker = cycleData['ticker']
        balances = cycleData['balances']
        catch = False

        if not catch and KLines is not None and ticker is not None and balances is not None:
            catch = False
            buys = self.data['buys'] # 已成交的买单，相当于开多单
            sells = self.data['sells'] # 已成交的卖单，相当于开空单
            print('balances:', balances)
            MAs = calcMAs(KLines, ma=30)
            _, ma = MAs[-1]
            buy1 = ticker[0]
            sell1 = ticker[1]
            last_price = ticker[-4]
            print('last_price && ma:', last_price, ma)
            if last_price > ma and len(buys) == 0:
                print('BUY')
                initBuyAmount = self.data['initBuyAmount'] = balances.get(self.data['money'], 0.0) / last_price * 0.001
                print('initBuyAmount', self.data['initBuyAmount'])
                if initBuyAmount > 0:
                    self.state = 'wait'
                    self.reactor.callWhenRunning(self.buy, sell1, initBuyAmount)
            elif last_price < ma and len(sells) == 0:
                print('SELL')
                initSellAmount = self.data['initSellAmount'] = balances.get(self.data['coin'], 0.0) * 0.001
                print('initSellAmount', self.data['initSellAmount'])
                if initSellAmount > 0:
                    self.state = 'wait'
                    self.reactor.callWhenRunning(self.sell, buy1, initSellAmount)

        if not catch and KLines is not None and ticker is not None:
            catch = False
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

            if llk_close > llb_d and lk_close < lb_d:
                print('BUYBOLL')
            elif llk_close < llb_u and lk_close > lb_u:
                print('SELLBOLL')

        if not catch:
            catch = False
            buyp = self.data['buyp'] # 未成交的卖单，相当于平多单
            sellp = self.data['sellp'] # 未成交的买单，相当于平空单
            if buyp is not None:
                buyp['check'] = False
                print('CHECK BUYP')
                self.state = 'wait_for_check'
            if sellp is not None:
                sellp['check'] = False
                print('CHECK SELLP')
                self.state = 'wait_for_check'



    def wait_for_check(self):
        buyp = self.data['buyp']
        sellp = self.data['sellp']
        if buyp['check'] and sellp['check']:
            self.state = 'run'

    def wait(self):
        pass




klinesCycle = Cycle(reactor, bitfinex.getKLineLastMin, 'klines', limit=1, wait=50, clean=False)
klinesCycle.start(pairs, last=30)
tickerCycle = Cycle(reactor, bitfinex.getTicker, 'ticker', limit=1, wait=3, clean=False)
tickerCycle.start(pairs)
balancesCycle = Cycle(reactor, bitfinex.getBalances, 'balances', limit=1, wait=2)
balancesCycle.start(list(pairs))

states = ['init', 'run', 'wait_for_check', 'wait']

bitfinexRobot = BitfinexRobot(reactor, states, [klinesCycle, tickerCycle, balancesCycle])
bitfinexRobot.start('init')
