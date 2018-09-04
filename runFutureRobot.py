import sys
import signal

from zope.interface import provider

from twisted.logger import Logger, ILogObserver, formatEvent, globalLogPublisher
from twisted.internet import threads, defer, task, reactor
from twisted.python.failure import Failure
from twisted.python import usage

from log import logger

from okexFutureRobot import RobotService
service = RobotService()# the main service

logObserver = logger()

log = Logger()

def defaultErrHandler(failure):
    log.error(failure)

### interactive module ###

CMD_STATUS = {
    'mode': 'background'
}

def ignoreKeyboardInterrupt():
    signal.signal(signal.SIGINT, lambda _1, _2: print())

def initCommandConfig():
    if CMD_STATUS['mode'] == 'foreground':
        globalLogPublisher.addObserver(logObserver)
    elif CMD_STATUS['mode'] == 'background':
        ignoreKeyboardInterrupt()

def getInput(prompt):
    if CMD_STATUS['mode'] == 'background':
        def inputHandler():
            command = input(prompt)
            return {
                'keyboard': False,
                'stdin': command,
            }
        d = threads.deferToThread(inputHandler)
    elif CMD_STATUS['mode'] == 'foreground':
        d = defer.Deferred()
        def KeyboardInterruptHandler(sig, frame):
            ignoreKeyboardInterrupt()
            d.callback({
                'keyboard': True,
                'stdin': '',
            })
        signal.signal(signal.SIGINT, KeyboardInterruptHandler)
    return d

def inputLoop():
    prompt = '||> '
    # indent = ' ' * len(prompt)

    d = getInput(prompt)

    def handler(msg):
        if msg['keyboard']:
            # set to background mode
            if CMD_STATUS['mode'] == 'background':
                print()
            else:
                globalLogPublisher.removeObserver(logObserver)
                CMD_STATUS['mode'] = 'background'
        else:
            command = msg['stdin'].split(' ')
            # print(command)
            if len(command) == 1:
                if command[0] == '':
                    return
                elif command[0] == 'foreground':
                    # set to foreground mode
                    print("switch to foreground mode\n"
                          "use 'Ctrl + C' to return to background mode\n")
                    globalLogPublisher.addObserver(logObserver)
                    CMD_STATUS['mode'] = 'foreground'
                    return
                elif command[0] == 'shutdown':
                    print('robot shut down...')
                    service.stopService()
                    reactor.stop()
                    return 'shutdown'
            print("unknown command, use 'help' to view the help message")
            #TODO

    d.addCallback(handler)
    d.addErrback(defaultErrHandler)

    def _next(msg):
        if msg != 'shutdown':
            reactor.callWhenRunning(inputLoop)
    d.addBoth(_next)

    return d

if __name__ == '__main__':
    service.startService()
    initCommandConfig()
    reactor.callWhenRunning(inputLoop)
    reactor.run()


