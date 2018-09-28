import subprocess
import time
from sys import argv


def writeBeat(filename, t, beat):
    staFile = open(filename, 'w+')
    staFile.write("%f,%s\n" % (t, beat))
    staFile.close()

def run(coin):
    logFilename = 'log/okex_' + coin
    beat = 'START'
    writeBeat(logFilename, time.time(), beat)
    p = subprocess.Popen(['python', 'runFutureRobot.py', coin, 'usdt'])
    return p

_, coin = argv
p = run(coin)

while True:
    time.sleep(1)
    logFilename = 'log/okex_' + coin
    logFile = open(logFilename, 'r+')
    lines = list(logFile.readlines())
    line = lines[-1]
    log = line.strip()
    logFile.close()

    ctrlFilename = 'log/okex_' + coin + '_ctrl'
    ctrlFile = open(ctrlFilename, 'r')
    lines = list(ctrlFile.readlines())
    line = lines[-1]
    ctrl = line.strip()
    ctrlFile.close()

    print(ctrlFilename, ctrl)

    t, status = log.split(',')
    t = float(t)
    if (time.time() - t) > 20 * 60 and (status == 'OK' or status == 'START') and not(ctrl == 'STOP'):
        print('RESTART')
        p.kill()
        p = run(coin)
    elif status == 'PPP' or ctrl == 'STOP':
        break

p.kill()


