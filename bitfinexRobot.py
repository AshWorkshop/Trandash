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

class BitfinexRobot(Robot):

    def run(self):
        cycleData = self.data['cycleData']
        klines = cycleData['klines']
        ticker = cycleData['ticker']
        catch = False

        if not catch and klines is not None and ticker is not None:
            catch = True
            MAs = calcMAs(klines, ma=30)
            _, ma = MAs[-1]
            last_price = ticker[-4]
            print('last_price && ma:', last_price, ma)

pairs = (coin, money)

klinesCycle = Cycle(reactor, bitfinex.getKLineLastMin, 'klines', limit=1, wait=50, clean=False)
klinesCycle.start(pairs, last=30)
tickerCycle = Cycle(reactor, bitfinex.getTicker, 'ticker', limit=1, wait=2)
tickerCycle.start(pairs)

states = ['run']

bitfinexRobot = BitfinexRobot(reactor, states, [klinesCycle, tickerCycle])
bitfinexRobot.start('run')
