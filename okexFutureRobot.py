from robots.base import RobotBase, CycleSource, Action, LoopSource
from twisted.internet import reactor, task
from twisted.application import service
from twisted.logger import Logger
from exchanges.okex.OKexService import okexFuture
from okexFutureSettings import pairs, rate, top, initAmount, delta, leverage, profitRate
from utils import calcMAs, calcBolls

import time
import datetime



def counter():
    log = Logger('counter')
    log.info('tick')

def isExpired(data, period=60):
    if data is None:
        return True
    dataTime, _ = data
    if (time.time() - dataTime) > 60:
        return True
    else:
        return False

def keyParse(keys):
    key_args = keys.split('?')
    if len(key_args) == 0:
        return (None, None)
    elif len(key_args) == 1:
        return (key_args[0], None)
    elif len(key_args) == 2:
        key = key_args[0]
        argPart = key_args[1]
        _args = argPart.split('&')
        args = {}
        for _arg in _args:
            kw, arg = _arg.split('=')
            args[kw] = arg
        return (key, args)

    return (None, None)


def getAvg(orders):
    total = 0
    totalAmount = 0
    for orderId, order in orders:
        price = order['price']
        amount = order['amount']
        amount = round(amount)
        total += price * amount
        totalAmount += amount
    if totalAmount == 0:
        return (0.0, 0.0)
    return (total / totalAmount, totalAmount)

    

class OKexFutureRobot(RobotBase):
    def launch(self, oldState, newState):
        global TIME
        actions = []
        #self.log.debug("{newState}", newState=newState)

        self.log.info('failedActions: {number}', number=len(newState.get('failedActions', [])))
        self.log.info('undoneActions: {number}', number=len(newState.get('actions', [])))

        for action in oldState['actions']:
            if action.wait:
                return []


        mas = newState.get('ma')
        tickers = newState.get('ticker')
        positions = newState.get('position')
        buys, sells = newState.get('orders', [None, None])
        buyp, sellp = newState.get('pOrders', [None, None])

        # 平单管理
        if buys is not None and sells is not None:
            buyFlag, sellFlag = (False, False)
            buypPrice, buypAmount = (0.0, 0.0)
            sellpPrice, sellpPrice = (0.0, 0.0)
            


        # 开单检测
        if buys is not None and sells is not None:
            for orderId, buy in buys.items():
                if buy['price'] is None or buy['amount'] is None:
                    self.log.info('ORDER_CHECK {orderId}', orderId=orderId)
                    action = Action(reactor, okexFuture.getOrder, 'check_buy?orderId=' + str(orderId), wait=True, payload={
                        'kwargs': {
                            'pairs': pairs,
                            'orderId': orderId
                        }
                    })
                    actions.append(action)

            for orderId, sell in sells.items():
                if sell['price'] is None or sell['amount'] is None:
                    self.log.info('ORDER_CHECK {orderId}', orderId=orderId)
                    action = Action(reactor, okexFuture.getOrder, 'check_sell?orderId=' + str(orderId), wait=True, payload={
                        'kwargs': {
                            'pairs': pairs,
                            'orderId': orderId
                        }
                    })
                    actions.append(action)

        # 初始单
        if not isExpired(mas) and not isExpired(tickers) and not isExpired(positions) and buys is not None and sells is not None:
            _, ma = mas
            _, ticker = tickers
            _, position = positions
            
            self.log.info("buys && sells: {buys} {sells}", buys=len(buys), sells=len(sells))

            buy_amount, sell_amount = position

            if ticker > ma and buy_amount == 0 and len(buys) == 0:
                self.log.info('BUY')
                action = Action(reactor, okexFuture.trade, 'buy?' + 'amount=' + str(initAmount), wait=True, payload={
                    'kwargs': {
                        'pairs': pairs,
                        'amount': str(round(initAmount)),
                        'tradeType': "1",
                        'matchPrice': "1"
                    }
                })
                actions.append(action)

            elif ticker < ma and sell_amount == 0 and len(sells) == 0:
                self.log.info('SELL')
                action = Action(reactor, okexFuture.trade, 'sell?' + 'amount=' + str(initAmount), wait=True, payload={
                    'kwargs': {
                        'pairs': pairs,
                        'amount': str(round(initAmount)),
                        'tradeType': "2",
                        'matchPrice': "1"
                    }
                })
                actions.append(action)

            

        self.log.info("{count}", count=newState.get('count'))
        

        self.log.info('newActions:{actions}', actions=len(actions))
        return actions


    def actionDoneHandler(self,state,actionDoneEvent):
        keys = actionDoneEvent.key
        key, args = keyParse(keys)
        data = actionDoneEvent.data
        newState = self.getNewState(state)
        if key is not None:
            if key == 'buy' and args is not None:
                # newState['orders'] = []
                newState['orders'][0] = state['orders'][0].copy()
                # newState['orders'][1] = state['orders'][1].copy()
                newState['orders'][0][str(data['data'])] = {
                    'price': None,
                    'amount': None
                }
                newState['lastAmount'] = args['amount']
            elif key == 'sell' and args is not None:
                # newState['orders'] = []
                # newState['orders'][0] = state['orders'][0].copy()
                newState['orders'][1] = state['orders'][1].copy()
                newState['orders'][1][str(data['data'])] = {
                    'price': None,
                    'amount': None
                }
                newState['lastAmount'] = args['amount']
            elif key == 'check_buy' and args is not None:
                orderId = args.get('orderId')
                if orderId is not None:
                    newState['orders'][0][orderId] = {
                        'price': data['data'][0].get('price'),
                        'amount': data['data'][0].get('amount')
                    }
            elif key == 'check_sell' and args is not None:
                orderId = args.get('orderId')
                if orderId is not None:
                    newState['orders'][1][orderId] = {
                        'price': data['data'][1].get('price'),
                        'amount': data['data'][1].get('amount')
                    }

        return newState

    def KLinesHandler(self, state, KLinesEvent):
        newState = self.getNewState(state)
        self.log.info('got KLinesEvent')
        KLines = KLinesEvent.data['data']
        MAs = calcMAs(KLines, ma=30)
        _, ma = MAs[-1]
        newState['ma'] = [time.time(), ma]

        return newState

    def tickerHandler(self, state, tickerEvent):
        newState = self.getNewState(state)
        self.log.info('got tickerEvent')
        tickers = tickerEvent.data['data']
        ticker = tickers['last']
        newState['ticker'] = [time.time(), ticker]

        return newState

    def positionHandler(self, state, positionEvent):
        newState = self.getNewState(state)
        self.log.info('got positionEvent')
        positions = positionEvent.data['data']
        position = [positions['buy_amount'], positions['sell_amount']]
        newState['position'] = [time.time(), position]

        return newState

    def orderBookHandler(self, state, orderBookEvent):
        newState = self.getNewState(state)
        self.log.info('got orderBookEvent')
        newState['orderBook'] = [time.time(), orderBookEvent.data['data']]

        return newState

    def userInfoHandler(self, state, userInfoEvent):
        newState = self.getNewState(state)
        self.log.info('got userInfoEvent')
        newState['userInfo'] = [time.time(), userInfoEvent.data['data']]

        return newState
    

    def tickHandler(self, state, tickEvent):
        newState = dict()
        newState.update(state)
        newState['count'] = state.get('count', 0) + 1

        return newState

    def systemEventHandler(self, state, systemEvent):
        newState = dict()
        newState.update(state)

        return newState

# gateioSource = CycleSource(reactor, gateio.getOrderBook, key='gateioOrderBooks', payload={
#     'args': [('eth', 'usdt')]
# })

KLinesSource = CycleSource(
    reactor,
    okexFuture.getKLineLastMin,
    'KLines',
    payload={
        'args': [pairs],
        'kwargs': {
            'last': 100
        }
    }
)
tickerSource = CycleSource(
    reactor,
    okexFuture.getTicker,
    'ticker',
    payload={
        'args': [pairs]
    }
)
positionSource = CycleSource(
    reactor,
    okexFuture.getPosition,
    'position',
    limit=5,
    payload={
        'args': [pairs]
    }
)
userInfoSource = CycleSource(
    reactor,
    okexFuture.getUserInfo,
    'userInfo',
    limit=5,
    payload={
        'args': [pairs[0]]
    }
)
orderBookSource = CycleSource(
    reactor,
    okexFuture.getOrderBook,
    'orderBook',
    payload={
        'args':[pairs]
    }
)



tickSource = LoopSource(
    reactor,
    counter
)

robot = OKexFutureRobot()

robot.bind(
    'tickEvent',
    robot.tickHandler
)

robot.bind(
    'actionDoneEvent',
    robot.actionDoneHandler,
)

robot.bind(
    'dataRecivedEvent',
    robot.KLinesHandler,
    'KLines'
)

robot.bind(
    'dataRecivedEvent',
    robot.tickerHandler,
    'ticker'
)

robot.bind(
    'dataRecivedEvent',
    robot.positionHandler,
    'position'
)

robot.bind(
    'dataRecivedEvent',
    robot.userInfoHandler,
    'userInfo'
)

robot.bind(
    'dataRecivedEvent',
    robot.orderBookHandler,
    'orderBook'
)

robot.state.update({
    'tickSource': tickSource,
    'orders': [{}, {}]
})

class RobotService(service.Service):
    log = Logger()
    def startService(self):
        global TIME
        TIME = time.time()
        self.log.info('starting robot service...')
        robot.listen([KLinesSource, tickerSource, positionSource, userInfoSource, orderBookSource, tickSource])
        
        KLinesSource.start()
        tickerSource.start()
        positionSource.start()
        userInfoSource.start()
        orderBookSource.start()
        tickSource.start()

    def stopService(self):
        self.log.info('stopping robot service...')
        KLinesSource.stop()
        tickerSource.stop()
        positionSource.stop()
        userInfoSource.stop()
        orderBookSource.stop()
        tickSource.stop()


if __name__ == "__main__":
    service  = RobotService()
    service.startService()