from twisted.internet import task
from twisted.internet import reactor
from twisted.python.failure import Failure
from exchanges.bitfinex.BitfinexService import bitfinex
import time
from sys import argv


from cycle.cycle import Cycle
from robots.robot import Robot

if len(argv) == 4:
    _, coin, money, dataFile = argv
else:
    print("ERROR!")
    quit()

orderHistoryCycle = Cycle(reactor, bitfinex.getOrderHistory, 'orderHistory')
states = ['run']

class BitfinexRobot(Robot):

    def run(self):
        cycleData = self.data['cycleData']
        orderHistory = cycleData['orderHistory']

        if orderHistory is not None:
            print('orderHistory:', orderHistory)

pairs = (coin, money)
orderHistoryCycle.start(pairs, float(time.time()), limits=5)
bitfinexRobot = BitfinexRobot(reactor, states, [orderHistoryCycle])
bitfinexRobot.start('run')
