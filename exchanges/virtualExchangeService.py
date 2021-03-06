from twisted.internet import defer, task
from twisted.python.failure import Failure

from exchanges.base import ExchangeService
from exchange import calcVirtualOrderBooks

import copy
import time

def defaultErrHandler(failure):
    print(failure.getBriefTraceback())
    return failure

def handleMultipleErr(data):
    flag = True
    for state, err in res:
        if not state:
            print(err)
            flag = False
    return flag

class OrderData(object):
    def __init__(self, orders=None):
        if orders is None:
            self._orders = {}
            self._newId = 0
        else:
            self._orders = orders
            self._newId = max(self._orders) + 1

    def resetNewId(self):
        self._newId = max(self._orders) + 1

    def _takeNewId(self):
        id = self._newId
        self._newId = self._newId + 1
        return id

    def getNewId(self):
        return self._newId

    def recordOrder(self, orderInfo):
        key = self._takeNewId()
        self._orders[key] = copy.deepcopy(orderInfo)
        return key

    def getOrder(self, orderId, defaultValue = None):
        return copy.deepcopy(self._orders.get(orderId, defaultValue))

    def getOrderRef(self, orderId, defaultValue = None):
        if orderId in self._orders:
            return self._orders[orderId]
        else:
            return defaultValue

    def getOrders(self):
        return copy.deepcopy(self._orders)

    def delOrder(self, orderId):
        if orderId in self._orders:
            del self._orders[orderId]

    def loadData(self, path):
        pass # TODO

    def saveData(self, path):
        pass # TODO

class VirtualExchange(ExchangeService):

    def __init__(self, exchange, mediums, orders = None):
        self.exchange = exchange

        if not isinstance(mediums, tuple):
            raise TypeError("type of 'mediums' must be 'tuple'")
        self.medium = mediums[0]

        self.orderBookData = None
        self.orderBookPairs = None
        if orders is None:
            self.orders = OrderData()
        else:
            self.orders = orders

        self.retryTimes = 3
        self.retryWaitTime = 1 # second

    def cleanOrderBookData(self):
        self.orderBookData = None

    def setMediums(self, mediums):
        if not isinstance(mediums, tuple):
            raise TypeError("type of 'medium' must be 'tuple'")
        self.medium = mediums[0]
        self.cleanOrderBookData()

    def getBalance(self, coin):
        return exchange.getBalance(coin)

    def getBalances(self, coins=None):
        return exchange.getBalances(coins)

    def getOrderState(self, statusA, statusB):
        unusual = ('error', 'cancelled')
        if statusA == 'done' and statusB == 'done':
            status = 'done'
        elif statusA == 'cancelled' and statusB == 'cancelled':
            status = 'cancelled'
        elif statusA in unusual or statusB in unusual: # TODO: could be improved
            status = 'error'
        else:
            status = 'open'
        return status

    def getOrderBook(self, pairs):
        self.orderBookPairs = pairs
        dA = self.exchange.getOrderBook( (pairs[0], self.medium) )
        dB = self.exchange.getOrderBook( (self.medium, pairs[1]) )

        d = defer.DeferredList( [dA, dB], consumeErrors=True)

        def handleBody(datas):
            (stateA, dataA), (stateB, dataB) = datas
            if stateA and stateB:
                virtualOB, medium = calcVirtualOrderBooks(dataA, dataB)
                self.orderBookData = (virtualOB, medium)
                return virtualOB
            else:
                for state, data in datas:
                    if not state:
                        print(data)
                self.cleanData()
                return None
        d.addCallback(handleBody)
        d.addErrback(defaultErrHandler)
        return d

    def buy(self, pairs, price, amount):
        data = self.orderBookData

        # check if data is available
        if data is None:
            d = defer.fail(Exception('No available order book data'))
        elif pairs != self.orderBookPairs:
            d = defer.fail(Exception("coin pairs 'pairs' does not match the order book data"))
        else:
            PRICE, AMOUNT = range(2)
            (_, sell), (_, mediumSell) = data

            overflow = False

            A = amount
            B = price * amount
            M = 0

            # calculate the amount of medium
            sumM = 0
            for l, order in enumerate(sell):
                s = sumM + order[AMOUNT]
                if s == A:
                    M = sum(mediumSell[:l + 1])
                    break
                elif s > A:
                    M = sum(mediumSell[:l]) + (A - sumM) / order[AMOUNT] * mediumSell[l]
                    break
                sumM = s
            else:
                overflow = True

            if overflow:
                d = defer.fail(Exception("'amount' is too big"))
            else:
                # initiate transaction
                symbol = self.exchange.getSymbol(pairs)

                dA = lambda :self.exchange.buy( (pairs[0], self.medium) , M / A, A)
                dB = lambda :self.exchange.buy( (self.medium, pairs[1]) , B / M, M)

                @defer.inlineCallbacks
                def transaction():
                    taskA, taskB = dA, dB
                    for t in range(1 + self.retryTimes):
                        res = yield defer.DeferredList( [taskA(), taskB()], consumeErrors=True)
                        (stateA, dataA), (stateB, dataB) = res
                        if stateA and stateB: # succeeded
                            break
                        time.sleep(self.retryWaitTime)
                        taskA, taskB = lambda: defer.succeed(dataA), lambda: defer.succeed(dataB)
                        if not stateA:
                            print(dataA)
                            print(f"start {pairs[0], self.medium} buy order failed")
                            print(f"retry times: {t}")
                            taskA = dA
                        if not stateB:
                            print(dataB)
                            print(f"start {self.medium, pairs[1]} buy order failed")
                            print(f"retry times: {t}")
                            taskB = dB
                    else:
                        print(f"out of retry times, starting buy order failed")
                        returnValue(None)

                    id = self.orders.recordOrder({
                        'orderId': (dataA, dataB),
                        'type': 'buy',
                        'initPrice': price,
                        'initAmount': amount,
                        'coinPair': symbol,
                        'status': 'open',
                    })
                    returnValue(id)
                d = transaction()

        d.addErrback(defaultErrHandler)
        return d

    def sell(self, pairs, price, amount):
        data = self.orderBookData

        # check if data is available
        if data is None:
            d = defer.fail(Exception('No available order book data'))
        elif pairs != self.orderBookPairs:
            d = defer.fail(Exception("coin pairs 'pairs' does not match the order book data"))
        else:
            PRICE, AMOUNT = range(2)
            (buy, _), (mediumBuy, _) = data

            overflow = False

            A = amount
            B = price * amount
            M = 0

            # calculate the amount of medium
            sumM = 0
            for l, order in enumerate(buy):
                s = sumM + order[AMOUNT]
                if s == A:
                    M = sum(mediumBuy[:l + 1])
                    break
                elif s > A:
                    M = sum(mediumBuy[:l]) + (A - sumM) / order[AMOUNT] * mediumBuy[l]
                    break
                sumM = s
            else:
                overflow = True

            if overflow:
                d = defer.fail(Exception("'amount' is too big"))
            else:
                # initiate transaction
                symbol = self.exchange.getSymbol(pairs)

                dA = lambda :self.exchange.sell( (pairs[0], self.medium) , M / A, A)
                dB = lambda :self.exchange.sell( (self.medium, pairs[1]) , B / M, M)

                @defer.inlineCallbacks
                def transaction():
                    taskA, taskB = dA, dB
                    for t in range(1 + self.retryTimes):
                        res = yield defer.DeferredList( [taskA(), taskB()], consumeErrors=True)
                        (stateA, dataA), (stateB, dataB) = res
                        if stateA and stateB: # succeeded
                            break
                        time.sleep(self.retryWaitTime)
                        taskA, taskB = lambda: defer.succeed(dataA), lambda: defer.succeed(dataB)
                        if not stateA:
                            print(dataA)
                            print(f"start {pairs[0], self.medium} sell order failed")
                            print(f"retry times: {t}")
                            taskA = dA
                        if not stateB:
                            print(dataB)
                            print(f"start {self.medium, pairs[1]} sell order failed")
                            print(f"retry times: {t}")
                            taskB = dB
                    else:
                        print(f"out of retry times, starting sell order failed")
                        returnValue(None)

                    id = self.orders.recordOrder({
                        'orderId': (dataA, dataB),
                        'type': 'sell',
                        'initPrice': price,
                        'initAmount': amount,
                        'coinPair': symbol,
                        'status': 'open',
                    })
                    returnValue(id)
                d = transaction()

        d.addErrback(defaultErrHandler)
        return d

    def getOrder(self, pairs, orderId, fromRemote=True):
        """method to query the order info with order id

        :param fromRemote: flag used to determine order data from obtained local or remote server
        """
        data = self.orders.getOrder(orderId)
        symbol = self.exchange.getSymbol(pairs)

        # check if the orderId exist
        if data is None:
            d = defer.fail(Exception('this orderId does not exist'))
        elif symbol != data['coinPair']:
            d = defer.fail(Exception("'pairs' does not match this order"))
        elif fromRemote:
            idA, idB = data['orderId']
            dA = self.exchange.getOrder( (pairs[0], self.medium), idA)
            dB = self.exchange.getOrder( (self.medium, pairs[1]), idB)

            d = defer.DeferredList( [dA, dB] , consumeErrors=True)

            def handleBody(res):
                if not handleMultipleErr(res):
                    return None

                (_, resA), (_, resB) = res

                statusA, statusB = resA['status'], resB['status']

                status = self.getOrderState(statusA, statusB)

                # update local data
                self.orders.getOrderRef(orderId)['status'] = status

                order = {
                    'orderId': orderId,
                    'type': data['type'],
                    'initPrice': data['initPrice'],
                    'initAmount': data['initAmount'],
                    'coinPair': symbol,
                    'status': status,
                }
                return order
            d.addCallback(handleBody)
        else:
            defer.succeed(data)

        d.addErrback(defaultErrHandler)
        return d

    def cancel(self, pairs, orderId):
        data = self.orders.getOrderRef(orderId)
        symbol = self.exchange.getSymbol(pairs)

        # check if the orderId exist
        if data is None:
            d = defer.fail(Exception('this orderId does not exist'))
        elif symbol != data['coinPair']:
            d = defer.fail(Exception("'pairs' does not match this order"))
        else:
            idA, idB = data['orderId']
            dA = self.exchange.cancel( (pairs[0], self.medium), idA)
            dB = self.exchange.cancel( (self.medium, pairs[1]), idB)

            d = defer.DeferredList( [dA, dB] , consumeErrors=True)
            def handleBody(res):
                if not handleMultipleErr(res):
                    return None

                (_, (stateA, dataA)), (_, (stateB, dataB)) = res
                if stateA and stateB:
                    data['status'] = 'cancelled'
                    return True
                else:
                    return False

        d.addErrback(defaultErrHandler)
        return d

if __name__ == '__main__':
    from exchanges.bitfinex.BitfinexService import bitfinex
    VirtualExchange(bitfinex, ('ETH',) )