from twisted.internet import task
from twisted.internet import reactor
from twisted.python.failure import Failure
from exchanges.bitfinex.BitfinexService import bitfinex


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


bitfinexRobot(reactor, states, [orderHistoryCycle])
# bitfinexRobot.start()
