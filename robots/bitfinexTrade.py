from twisted.internet import task
from twisted.internet import reactor

from exchanges.bitfinex.BitfinexService import bitfinex
from twisted.python.failure import Failure

from cycle.cycle import Cycle

if len(argv) == 4:
    _, coin, money, dataFile = argvabs
else:
    print("ERROR!")
    quit()
