import sys, time
from datetime import datetime
from zope.interface import provider
from twisted.logger import LogLevelFilterPredicate, LogLevel
from twisted.logger import Logger, formatEvent, globalLogBeginner, globalLogPublisher
from twisted.logger import FileLogObserver, FilteringLogObserver

def formator(event):
    if event['log_namespace'] != 'log_legacy':
        sourceAndLevel = f"{event['log_namespace']}#{event['log_level'].name}"
    else:
        sourceAndLevel = '-'
    return f"{datetime.fromtimestamp(event['log_time']):%Y-%m-%dT%H:%M:%S%z} [{sourceAndLevel}] {formatEvent(event)}\n"

def logger():
    predicate = LogLevelFilterPredicate(LogLevel.debug)
    return FilteringLogObserver(FileLogObserver(sys.stdout, formator), [predicate])
