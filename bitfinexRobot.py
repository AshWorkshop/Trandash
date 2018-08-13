from twisted.internet import task
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

klinesCycle = Cycle(reactor, bitfinex.getKLineLastMin, 'klines', limit=1, wait=50, clean=False)
states = ['run']

class BitfinexRobot(Robot):

    def run(self):
        cycleData = self.data['cycleData']
        klines = cycleData['klines']

        if klines is not None:
            MAs = calcMAs(klines, ma=30)
            ma = MAs[-1]
            print('ma:', ma)

pairs = (coin, money)
klinesCycle.start(pairs, last=30)
bitfinexRobot = BitfinexRobot(reactor, states, [klinesCycle])
bitfinexRobot.start('run')
