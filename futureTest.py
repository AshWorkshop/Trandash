
from exchanges.okex.OKexService import okexFuture
# from exchanges.huobi.HuobiproService import huobipro
# from exchanges.gateio.GateIOService import gateio
# from exchanges.bitfinex.BitfinexService import bitfinex
from exchanges.sisty.sisty_key import MD5Key
from exchanges.sisty.SistyService import sisty
from requestUtils.request import get, post


from twisted.internet import reactor

from cycle.cycle import Cycle

import urllib
import hashlib
import time

pairs = ('eth', 'usdt')

start = time.time()


tickerCycle = Cycle(reactor, sisty.getUserInfo, 'test')
tickerCycle.start()
# reactor.callWhenRunning(test)
reactor.run()
