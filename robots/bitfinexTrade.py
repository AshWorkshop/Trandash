from twisted.internet import task
from twisted.internet import reactor

from exchanges.bitfinex.BitfinexService import bitfinex
from twisted.python.failure import Failure

from cycle.cycle import Cycle

if len(argv) == 4:
    _, coin, money, dataFile = argv
else:
    print("ERROR!")
    quit()

state = dict()
state['status'] = 'INIT' # INIT: 初始化
