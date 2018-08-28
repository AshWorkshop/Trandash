import sys, time
from datetime import datetime
from zope.interface import provider
from twisted.logger import Logger, ILogObserver, formatEvent, globalLogBeginner, FileLogObserver

def formator(event):
    if event['log_namespace'] != 'log_legacy':
        sourceAndLevel = f"{event['log_namespace']}#{event['log_level'].name}"
    else:
        sourceAndLevel = '-'
    return f"{datetime.fromtimestamp(event['log_time']):%Y-%m-%dT%H:%M:%S%z} [{sourceAndLevel}] {formatEvent(event)}\n"

def logger():
    return FileLogObserver(sys.stdout, formator)
