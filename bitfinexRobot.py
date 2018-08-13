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

klinesCycle = Cycle(reactor, bitfinex.getKLineLastMin, 'klines')
states = ['run']

class BitfinexRobot(Robot):

    def run(self):
        cycleData = self.data['cycleData']
        klines = cycleData['klines']

        if klines is not None:
            print('klines:', klines)

pairs = (coin, money)
klinesCycle.start(pairs, last=30)
bitfinexRobot = BitfinexRobot(reactor, states, [klinesCycle])
bitfinexRobot.start('run')
