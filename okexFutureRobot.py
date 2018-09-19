from robots.base import RobotBase, CycleSource, Action, LoopSource
from twisted.internet import reactor, task, defer
from twisted.application import service
from twisted.logger import Logger
from exchanges.okex.OKexService import okexFuture
from okexFutureSettings import pairs, rate, top, defaultInitAmount, delta, leverage, profitRate, useInitDelta, lossLimit, amountRate
from utils import calcMAs, calcBolls
from twisted.python.failure import Failure

import time
import datetime
import shelve
from sys import argv

if len(argv) == 3:
    _, coin, money = argv
    pairs = [coin, money]
    print(pairs)


@defer.inlineCallbacks
def buyp(amount, price=""):
    orderId = None
    try:
        if price == "":
            matchPrice = "1"
        else:
            matchPrice = "0"
        orderId = yield okexFuture.trade(pairs, price=price, amount=str(round(amount)), tradeType="3", matchPrice=matchPrice)
    except Exception as err:
        failure = Failure(err)
        return failure

    if orderId:
        try:
            order = yield okexFuture.getOrder(pairs, orderId=orderId)
        except Exception as err:
            failure = Failure(err)
            return None
        else:
            price = order[0]['price']
            return (orderId, price, float(amount))

@defer.inlineCallbacks
def sellp(amount, price=""):
    orderId = None
    try:
        if price == "":
            matchPrice = "1"
        else:
            matchPrice = "0"
        orderId = yield okexFuture.trade(pairs, price=price, amount=str(round(amount)), tradeType="4", matchPrice=matchPrice)
    except Exception as err:
        failure = Failure(err)
        return failure

    if orderId:
        try:
            order = yield okexFuture.getOrder(pairs, orderId=orderId)
        except Exception as err:
            failure = Failure(err)
            return failure
        else:
            price = order[0]['price']
            return (orderId, price, float(amount))



@defer.inlineCallbacks
def buy(amount=1.0, price="", totalAmount=0, avgPrice=0):
    orderId = None
    buyInfo = None
    try:
        if price:
            matchPrice = "0"
        else:
            matchPrice = "1"
        orderId = yield okexFuture.trade(pairs, price=price, amount=str(round(amount)), tradeType="1", matchPrice=matchPrice)
    except Exception as err:
        failure = Failure(err)
        return failure

    try:
        orders = yield okexFuture.getOrder(pairs, status="1", orderId="-1")
    except Exception as err:
        log = Logger('action')
        failure = Failure(err)
        log.info("{failure}", failure=failure)
    else:
        if orders is not None:
            for order in orders:
                orderType = order['type']
                status = order['status']
                pId = order['order_id']
                if (orderType == 1 or orderType == 3) and (status == 0 or status == 1):
                    log = Logger('buypc')
                    log.info("{pId}", pId=pId)
                    try:
                        result, data = yield okexFuture.cancel(pairs, orderId=pId)
                    except Exception as err:
                        failure = Failure(err)

    if orderId:
        try:
            order = yield okexFuture.getOrder(pairs, orderId=orderId)
        except Exception as err:
            failure = Failure(err)
            return failure
        else:
            price = order[0]['price']
            buyInfo = (orderId, price, float(amount))
            avgPrice = avgPrice * totalAmount + price * round(float(amount))
            totalAmount += round(float(amount))
            avgPrice = avgPrice / totalAmount
            buypInfo = yield buyp(amount=totalAmount, price=str(float(avgPrice) * (1 + profitRate / leverage)))
            # buypInfo = None
            return (buyInfo, buypInfo)
            
        

@defer.inlineCallbacks
def sell(amount=1.0, price="", totalAmount=0, avgPrice=0):
    orderId = None
    try:
        if price:
            matchPrice = "0"
        else:
            matchPrice = "1"
        orderId = yield okexFuture.trade(pairs, price=price, amount=str(round(amount)), tradeType="2", matchPrice=matchPrice)
    except Exception as err:
        failure = Failure(err)
        return failure

    try:
        orders = yield okexFuture.getOrder(pairs, status="1", orderId="-1")
    except Exception as err:
        log = Logger('action')
        failure = Failure(err)
        log.info("{failure}", failure=failure)
        
    else:
        if orders is not None:
            for order in orders:
                orderType = order['type']
                status = order['status']
                pId = order['order_id']
                if (orderType == 2 or orderType == 4) and (status == 0 or status == 1):
                    log = Logger('sellpc')
                    log.info("{pId}", pId=pId)
                    try:
                        result, data = yield okexFuture.cancel(pairs, orderId=pId)
                    except Exception as err:
                        failure = Failure(err)

    if orderId:
        try:
            order = yield okexFuture.getOrder(pairs, orderId=orderId)
        except Exception as err:
            failure = Failure(err)
            return failure
        else:
            price = order[0]['price']
            sellInfo = (orderId, price, float(amount))
            avgPrice = avgPrice * totalAmount + price * round(float(amount))
            totalAmount += round(float(amount))
            avgPrice = avgPrice / totalAmount
            sellpInfo = yield sellp(amount=totalAmount, price=str(float(avgPrice) * (1 - profitRate / leverage)))
            # sellpInfo = None
            return (sellInfo, sellpInfo)

@defer.inlineCallbacks
def cancle_p(pType="buy", avgPrice=0.0, totalAmount=0.0, must=False):
    orders = None
    try:
        orders = yield okexFuture.getOrder(pairs, status="1", orderId="-1")
    except Exception as err:
        print('cp1')
        log = Logger('cancle_p')
        failure = Failure(err)
        log.info("{failure}", failure=failure)
    else:
        if pType == 'buy':
            pType = 3
        elif pType == 'sell':
            pType = 4

        print(orders)
        if orders:
            for order in orders:
                orderType = order['type']
                status = order['status']
                pId = order['order_id']

                if orderType == pType and (status == 0 or status == 1):
                    log = Logger('pc')
                    log.info("{pId}", pId=pId)
                    try:
                        result, data = yield okexFuture.cancel(pairs, orderId=pId)
                    except Exception as err:
                        failure = Failure(err)

        pInfo = None
        try:
            if pType == 3:
                if not must:
                    pInfo = yield buyp(amount=totalAmount, price=str(avgPrice * (1 + profitRate / leverage)))
                else:
                    pInfo = yield buyp(amount=totalAmount)
            elif pType == 4:
                if not must:
                    pInfo = yield sellp(amount=totalAmount, price=str(avgPrice * (1 - profitRate / leverage)))
                else:
                    pInfo = yield sellp(amount=totalAmount)
        except Exception as err:
            log = Logger('cancle_p')
            failure = Failure(err)
            log.info("{failure}", failure=failure)
            return failure
        else:
            return pInfo


def counter():
    log = Logger('counter')
    log.info('tick')

def writeAccountRight(filename, t, right, unreal):
    staFile = open(filename, 'a+')
    staFile.write("%f,%f,%f\n" % (t, right, unreal))
    staFile.close()

def isExpired(data, period=2):
    if data is None:
        return True
    dataTime, _ = data
    if (time.time() - dataTime) > period:
        return True
    else:
        return not bool(data)

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

def searchLastAmount(amount, initAmount=1.0, rate=1.618, top=6):
    total = 0.0
    factor = 0
    if amount == 0.0:
        return 0.0
    for i in range(round(amount)):
        if i < top:
            factor = i
        else:
            factor = top - 1
        total += round(initAmount * rate ** factor)
        if total >= amount:
            break
    return initAmount * rate ** factor


class OKexFutureRobot(RobotBase):
    def launch(self, oldState, newState):
        global TIME
        actions = []
        #self.log.debug("{newState}", newState=newState)

        self.log.info('failedActions: {number}', number=len(newState.get('failedActions', [])))
        self.log.info('undoneActions: {number}', number=len(newState.get('actions', [])))

        for action in newState['actions']:
            if action.wait:
                return []


        mas = newState.get('ma')
        initAmount = newState.get('initAmount', defaultInitAmount)
        orderBooks = newState.get('orderBook')
        Bolls = newState.get('Bolls')
        KLines = newState.get('KLines')
        tickers = newState.get('ticker')
        buysells = newState.get('buysell')
        startTime = newState.get('startTime', 0.0)
        lastBuyAmount = newState.get('lastBuyAmount', 0.0)
        lastSellAmount = newState.get('lastSellAmount', 0.0)
        lastBuyPrice = newState.get('lastBuyPrice', 0.0)
        lastSellPrice = newState.get('lastSellPrice', 0.0)
        buyDelta = newState.get('buyDelta', delta)
        sellDelta = newState.get('sellDelta', delta)
        positions = newState.get('position')
        initBuyFlag = newState.get('initBuyFlag', True)
        initSellFlag = newState.get('initSellFlag', True)
        userInfos = newState.get('userInfo')

        self.log.info("{a} {b} {c} {d} {e}", a=isExpired(KLines, period=50), b=isExpired(tickers), c=isExpired(positions), d=isExpired(userInfos), e=isExpired(orderBooks))
        self.log.info("buyDelta && sellDelta: {buy} {sell}", buy=newState.get('buyDelta'), sell=newState.get('sellDelta'))
        self.log.info("initAmount: {amount}", amount=initAmount)
        # 初始单
        isInit = False
        if not isExpired(mas, period=50) and not isExpired(tickers) and not isExpired(positions) and not isExpired(orderBooks):
            _, ma = mas
            _, ticker = tickers
            _, position = positions
            _, buysell = buysells
            _, orderBook = orderBooks
            bids, asks = orderBook
            buy1, sell1 = buysell

            buy2, _ = bids[1]
            self.log.info('buy2:{buy}', buy=buy2)

            sell2, _ = asks[1]
            self.log.info('sell2:{sell}', sell=sell2)

            buy_amount, sell_amount, buy_avg_price, sell_avg_price, _, _ = position
            self.log.info("ma && ticker: {ma} {ticker}", ma=ma, ticker=ticker)
            self.log.info("buy && sell: {buy_amount} {sell_amount}", buy_amount=buy_amount, sell_amount=sell_amount)
            action = None
            if ticker > ma and buy_amount == 0 and initBuyFlag:
                action = Action(reactor, buy, key='buy?init=True', wait=True, payload={
                    'kwargs': {
                        'amount': initAmount,
                        'price': buy1,
                        'totalAmount': buy_amount,
                        'avgPrice': buy_avg_price
                    }
                })
            elif ticker < ma and sell_amount == 0 and initSellFlag:
                action = Action(reactor, sell, key='sell?init=True', wait=True, payload={
                    'kwargs': {
                        'amount': initAmount,
                        'price': sell1,
                        'totalAmount': sell_amount,
                        'avgPrice': sell_avg_price
                    }
                })

            if action:
                isInit = True
                actions.append(action)

        if not isInit and not isExpired(Bolls, period=50) and not isExpired(KLines, period=50) and not isExpired(positions) and not isExpired(tickers):
            _, ticker = tickers
            _, position = positions
            buy_amount, sell_amount, buy_avg_price, sell_avg_price, _, _ = position
            _, KLines = KLines
            _, Bolls = Bolls
            klines = KLines[-3:]
            bolls = Bolls[-3:]
            llk, lk, k = klines
            llb, lb, b = bolls
            _, _, _, _, llk_close, _, _ = llk
            _, _, _, _, lk_close, _, _ = lk
            _, llb_u, _, llb_d = llb
            _, lb_u, _, lb_d = lb
            _, b_u, _, b_d = b
            action = None
            self.log.info('llk_close && lk_close: {l1} {l2}', l1=llk_close, l2=lk_close)
            self.log.info('llb_d && lb_d: {l1} {l2}', l1=llb_d, l2=lb_d)
            if llk_close > llb_d and lk_close < lb_d:
                self.log.info('BUYBOLL lastBuyPrice: {price}', price=lastBuyPrice)
                if buy_amount > 0 and lastBuyPrice > 0:
                    bollRate = (lastBuyPrice - ticker) / lastBuyPrice
                    self.log.info("bollRate && delta: {bollRate}, {delta}", bollRate=bollRate, delta=buyDelta)
                    if bollRate > buyDelta or (useInitDelta and bollRate > delta):
                        self.log.info("lastBuyAmount: {amount}", amount=lastBuyAmount)
                        if lastBuyAmount < initAmount * rate ** top:
                            newBuyAmount = lastBuyAmount * rate
                        else:
                            newBuyAmount = lastBuyAmount
                        self.log.info("newBuyAmount: {amount}", amount=newBuyAmount)

                        action = Action(reactor, buy, key='buy?init=False', wait=True, payload={
                            'kwargs': {
                                'amount': newBuyAmount,
                                'totalAmount': buy_amount,
                                'avgPrice': buy_avg_price
                            }
                        })
                        # newState['buyDelta'] = bollRate
            elif llk_close < llb_u and lk_close > lb_u:
                self.log.info('SELLBOLL lastSellPrice: {price}', price=lastSellPrice)
                if sell_amount > 0 and lastSellPrice > 0:
                    bollRate = (ticker - lastSellPrice) / lastSellPrice
                    self.log.info("bollRate && delta: {bollRate}, {delta}", bollRate=bollRate, delta=sellDelta)
                    if bollRate > sellDelta or (useInitDelta and bollRate > delta):
                        self.log.info("lastSellAmount: {amount}", amount=lastSellAmount)
                        if lastSellAmount < initAmount * rate ** top:
                            newSellAmount = lastSellAmount * rate
                        else:
                            newSellAmount = lastSellAmount
                        self.log.info("newSellAmount: {amount}", amount=newSellAmount)

                        action = Action(reactor, sell, key='sell?init=False', wait=True, payload={
                            'kwargs': {
                                'amount': newSellAmount,
                                'totalAmount': sell_amount,
                                'avgPrice': sell_avg_price
                            }
                        })

            if action:
                actions.append(action)

        # 检查并挂平单        
        if not isExpired(positions):
            _, position = positions
            buy_amount, sell_amount, buy_avg_price, sell_avg_price, buy_available, sell_available = position
            self.log.info("buy_available && sell_available: {buy} {sell}", buy=buy_available, sell=sell_available)
            self.log.info('lastBuyPrice && lastSellPrice: {buy} {sell}', buy=lastBuyPrice, sell=lastSellPrice)
            self.log.info('lastBuyAmount && lastSellAmount: {buy} {sell}', buy=lastBuyAmount, sell=lastSellAmount)
            self.log.info('lastBuyDelta && lastSellDelta: {buy} {sell}', buy=buyDelta, sell=sellDelta)
            if buy_available != 0:
                action = Action(
                    reactor,
                    cancle_p,
                    key="cancle_p",
                    wait=True,
                    payload={
                        'kwargs': {
                            'pType': 'buy',
                            'avgPrice': buy_avg_price,
                            'totalAmount': buy_amount
                        }
                    }
                )
                actions.append(action)
            
            if sell_available != 0:
                action = Action(
                    reactor,
                    cancle_p,
                    key="cancle_p",
                    wait=True,
                    payload={
                        'kwargs': {
                            'pType': 'sell',
                            'avgPrice': sell_avg_price,
                            'totalAmount': sell_amount
                        }
                    }
                )
                actions.append(action)

        if not isExpired(userInfos) and not isExpired(positions):
            t, userInfo = userInfos
            if not userInfo:
                return actions
            _, position = positions
            buy_amount, sell_amount, buy_avg_price, sell_avg_price, buy_available, sell_available = position
            filename = 'data/' + 'okex_' + pairs[0] + '_' + str(startTime)
            writeAccountRight(filename, t, userInfo.get('account_rights', 0.0), userInfo.get('profit_unreal', 0.0))
            lossRate = newState.get('lossRate', 0.0)
            self.log.info('lossRate: {rate}', rate=lossRate)
            if lossRate > lossLimit:
                if buy_amount > 0:
                    key = "ppp?wait=False"
                    if sell_amount > 0:
                        key = "ppp?wait=True"
                    else:
                        key = "ppp?wait=False"
                    action = Action(
                    reactor,
                    cancle_p,
                    key=key,
                    wait=True,
                    payload={
                            'kwargs': {
                                'pType': 'buy',
                                'avgPrice': buy_avg_price,
                                'totalAmount': buy_amount,
                                'must': True
                            }
                        }
                    )
                    actions.append(action)
                if sell_amount > 0:
                    key = "ppp?wait=False"
                    if buy_amount > 0:
                        key = "ppp?wait=True"
                    action = Action(
                        reactor,
                        cancle_p,
                        key=key,
                        wait=True,
                        payload={
                            'kwargs': {
                                'pType': 'sell',
                                'avgPrice': sell_avg_price,
                                'totalAmount': sell_amount,
                                'must': True
                        }
                        }
                    )
                    actions.append(action)


        self.log.info("{count}", count=newState.get('count'))
        

        self.log.info('newActions: {actions}', actions=len(actions))
        return actions


    def actionDoneHandler(self,state,actionDoneEvent):
        keys = actionDoneEvent.key
        key, args = keyParse(keys)
        data = actionDoneEvent.data
        newState = self.getNewState(state)
        if key is not None:
            if key == 'buy':
                buyInfo, buypInfo = data['data']
                self.log.info("buyInfo: {info}", info=buyInfo)
                _, price, amount = buyInfo
                self.log.info("got buy: {price} {amount}", price=price, amount=amount)
                self.log.info("buypInfo: {info}", info=buypInfo)
                buyDelta = delta
                lastBuyPrice = newState.get('lastBuyPrice', 0)
                if lastBuyPrice > 0:
                    buyDelta = (lastBuyPrice - price) / lastBuyPrice
                    self.log.info("buyDelta: {delta}", delta=buyDelta)
                newState['lastBuyPrice'] = price
                newState['lastBuyAmount'] = amount
                
                if args is not None:
                    init = args['init']
                    if init == 'True':
                        newState['buyDelta'] = delta
                        newState['initBuyFlag'] = False
                    else:
                        newState['buyDelta'] = buyDelta
            elif key == 'sell':
                sellInfo, sellpInfo = data['data']
                self.log.info("sellInfo: {info}", info=sellInfo)
                _, price, amount = sellInfo
                self.log.info("got sell: {price} {amount}", price=price, amount=amount)
                self.log.info("sellpInfo: {info}", info=sellpInfo)
                sellDelta = delta
                lastSellPrice = newState.get('lastSellPrice', 0)
                if lastSellPrice > 0:
                    sellDelta = (price - lastSellPrice) / lastSellPrice
                    self.log.info("sellDelta: {delta}", delta=sellDelta)
                newState['lastSellPrice'] = price
                newState['lastSellAmount'] = amount
                
                if args is not None:
                    init = args['init']
                    if init == 'True':
                        newState['sellDelta'] = delta
                        newState['initSellFlag'] = False
                    else:
                        newState['sellDelta'] = sellDelta

            elif key == "ppp":
                if args:
                    if args.get('wait', False):
                        newState['pppCount'] = newState.get('pppCount', 0) + 1
                        if newState['pppCount'] == 2:
                            reactor.stop()
                    else:
                        reactor.stop()
                else:
                    reactor.stop()
            
        return newState

    def KLinesHandler(self, state, KLinesEvent):
        newState = self.getNewState(state)
        self.log.info('got KLinesEvent')
        KLines = KLinesEvent.data['data']
        if KLines:
            MAs = calcMAs(KLines, ma=30)
            Bolls = calcBolls(KLines, ma=20)
        else:
            return newState
        _, ma = MAs[-1]
        newState['ma'] = [time.time(), ma]
        newState['Bolls'] = [time.time(), Bolls]
        newState['KLines'] = [time.time(), KLines]

        return newState

    def tickerHandler(self, state, tickerEvent):
        newState = self.getNewState(state)
        self.log.info('got tickerEvent')
        tickers = tickerEvent.data['data']
        if tickers is None:
            ticker = None
        else:
            ticker = tickers['last']
            buysell = (tickers['buy'], tickers['sell'])
        newState['ticker'] = [time.time(), ticker]
        newState['buysell'] = [time.time(), buysell]

        return newState

    def positionHandler(self, state, positionEvent):
        newState = self.getNewState(state)
        self.log.info('got positionEvent')
        positions = positionEvent.data['data']
        if positions is None:
            return newState
        position = [
                        positions['buy_amount'],
                        positions['sell_amount'],
                        positions['buy_price_avg'],
                        positions['sell_price_avg'],
                        positions['buy_available'],
                        positions['sell_available']
                    ]
        newState['position'] = [time.time(), position]
        lastBuyAmount = newState.get('lastBuyAmount', 0.0)
        lastSellAmount = newState.get('lastSellAmount', 0.0)
        lastBuyPrice = newState.get('lastBuyPrice', 0.0)
        lastSellPrice = newState.get('lastSellPrice', 0.0)
        initAmount = newState.get('initAmount', defaultInitAmount)



        if lastBuyPrice == 0 and position[0] > 0:
            lastBuyPrice = position[2]
            lastBuyAmount = position[0]
            newState['lastBuyPrice'] = lastBuyPrice
            newState['lastBuyAmount'] = searchLastAmount(lastBuyAmount, initAmount=initAmount, rate=rate, top=top)
        if lastSellPrice == 0 and position[1] > 0:
            lastSellPrice = position[3]
            lastSellAmount = position[1]
            newState['lastSellPrice'] = lastSellPrice
            newState['lastSellAmount'] = searchLastAmount(lastSellAmount, initAmount=initAmount, rate=rate, top=top)

        return newState

    def orderBookHandler(self, state, orderBookEvent):
        newState = self.getNewState(state)
        self.log.info('got orderBookEvent')
        newState['orderBook'] = [time.time(), orderBookEvent.data['data']]

        return newState

    def userInfoHandler(self, state, userInfoEvent):
        newState = self.getNewState(state)
        self.log.info('got userInfoEvent')
        userInfo = userInfoEvent.data['data']
        newState['userInfo'] = [time.time(), userInfo]

        if not userInfo:
            return newState

        accountRight = userInfo['account_rights']
        profit_unreal = userInfo['profit_unreal']
        keep_deposit = userInfo['keep_deposit']
        _, ticker = newState.get('ticker', (None, 0.0))

        if ticker:
            balance = accountRight - profit_unreal - keep_deposit
            initAmount = balance * ticker * leverage / 10 * amountRate
            if initAmount < 1.0:
                initAmount = 1.0
            newState['initAmount'] = initAmount
        
        if accountRight > newState.get('maxRight', 0.0):
            newState['maxRight'] = accountRight

        lossRate = 0.0
        if newState.get('maxRight', 0.0) > 0:
            lossRate = (newState['maxRight'] - accountRight) / newState['maxRight']
            newState['lossRate'] = lossRate
            if lossRate <= lossLimit:
                newState['pppCount'] = 0

        return newState
    

    def tickHandler(self, state, tickEvent):
        newState = dict()
        newState.update(state)
        newState['count'] = state.get('count', 0) + 1
        if newState['count'] % 10 == 0:
            newState['initBuyFlag'] = True
            newState['initSellFlag'] = True

        aliveActions = []

        for action in newState.get('actions', []):
            if time.time() <= action.time + 60 * 1:
                aliveActions.append(action)
        
        newState['actions'] = aliveActions

        # data = shelve.open(pairs[0] + "_db")
        # data['state'] = newState
        # data.close()

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
    limit=2,
    payload={
        'args': [pairs]
    }
)
userInfoSource = CycleSource(
    reactor,
    okexFuture.getUserInfo,
    'userInfo',
    limit=2,
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

# data = shelve.open(pairs[0] + '_db')
# state = data.get('state', {})
# data.close()
# robot.state.update(state)

robot.state.update({
    'tickSource': tickSource,
    'startTime': round(time.time()),
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