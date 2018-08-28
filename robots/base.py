from twisted.internet import task
from twisted.logger import Logger

import time

class RobotBase(object):
    log = Logger()
    
    def __init__(self):
        self.state = dict()  # 机器人状态
        self.state['actions'] = list() # 机器人动作执行列表
        self.binds = list()  # 事件绑定列表
        self.bind('actionDoneEvent', self._actionDoneHandler)
        self.bind('actionFailureEvent', self._actionFailureHandler)
        self.bind('systemEvent', self.systemEventHandler)
        self.doLastWork = False
        self.lastWork = None
        self.lastWorkArgs = None
        self.lastWorkKwargs = None

    def listen(self, sources):
        if isinstance(sources, list):
            for source in sources:
                source.addListener(self)
            
            self.activeSystemEvent(
                'LISTEN_STARTED',
                info={
                    'source': None,
                    'sources': sources
                }
            )

        else:
            sources.addListener(self)
            self.activeSystemEvent(
                'LISTEN_STARTED',
                info={
                    'source': sources,
                    'sources': None
                }
            )

    def stopListen(self, source):
        if source is not None:
            if source.removeListener(self):
                self.activeSystemEvent(
                    'LISTEN_STOPPED',
                    info={
                        'source': source
                    }
                )

    def bind(self, eventType, handler, key=None):
        _bind = {
            'handler': handler,
            'eventType': eventType,
            'key': key
        }
        self.binds.append(_bind)

    def _setLastWork(self, func, *args, **kwargs):
        self.lastWork = func
        self.lastWorkArgs = args
        self.lastWorkKwargs = kwargs
        self.doLastWork = True
    
    def _resetLastWork(self):
        self.lastWork = None
        self.lastWorkArgs = None
        self.lastWorkKwargs = None
        self.doLastWork = False

    def _doLastWork(self):
        if self.doLastWork:
            self.doLastWork = False
            self.lastWork(*self.lastWorkArgs, **self.lastWorkKwargs)

    def activeEvent(self, event):  # 以同步的方式触发事件
        self.log.info("{event!s}", event=event)
        self._setLastWork(self.cbListen, event)

    def activeSystemEvent(self, sysEventType, info={}):
        return self.activeEvent(Event(
            'systemEvent',
            data={
                'type': sysEventType,
                'info': info
            }
        ))

    # IListener
    def cbListen(self, event):  # 以异步的方式触发事件
        self.dispatch(event)

        return event

    def ebListen(self, failure):
        self.log.error("{failure!s}", failure=failure)

        return failure

    def dispatch(self, event):
        _handlers = list()

        for _bind in self.binds:
            if _bind['eventType'] == event.eventType:
                if _bind['key'] is None or _bind['key'] == event.key:
                    _handlers.append(_bind['handler'])

        newState = dict()
        newState.update(self.state)

        for handler in _handlers:
            _newState = handler(newState, event)
            newState.update(_newState)

        if newState != dict():
            self._launch(newState)

    def launch(self, oldState, newState):
        return list()

    def _launch(self, newState):
        actions = self.launch(self.state, newState)
        self.state.update(newState)
        for action in actions:
            self.state['actions'].append(action)
        for action in actions:
            action.addListener(self)
            action.start()

        self.state['failedActions'] = list()

        self._doLastWork()
        
        
    def _actionDoneHandler(self, state, actionDoneEvent):
        newState = dict()
        newState.update(state)
        newState['actions'] = list()
        for action in state['actions']:
            if action != actionDoneEvent.data['action']:
                newState['actions'].append(action)
        # self.log.warn("undone actions:{actions}", actions=len(newState['actions']))
        return newState

    def _actionFailureHandler(self, state, actionFailureEvent):
        newState = dict()
        newState.update(state)
        newState['actions'] = list()
        newState['failedActions'] = list()
        for action in state['actions']:
            if action != actionFailureEvent.data['action']:
                newState['actions'].append(action)

        for action in state['failedActions']:
            newState['failedActions'].append(action)

        newState['failedActions'].append(actionFailureEvent.data['action'])
        return newState

    def systemEventHandler(self, state, systemEvent):
        newState = dict()
        newState.update(state)
        return newState



class Event(object):

    def __init__(self, eventType, data=None, key=None):
        self.eventType = eventType
        self.key = key
        self.data = data

    def __str__(self):
        return "Event(eventType: %s, key: %s)" % (self.eventType, self.key)


class ISource(object):

    def addListener(self, listener):
        pass

    def removeListener(self, listener):
        pass

    def cbEvent(self, data):
        pass

    def ebEvent(self, failure):
        pass


class Action(object):
    log = Logger()

    def __init__(self, reactor, func, key=None, wait=False, payload=dict()):
        self.args = payload.get('args', [])
        self.kwargs = payload.get('kwargs', {})
        self.func = func
        self.key = key
        self.wait = wait
        self.listeners = list()
        self.reactor = reactor

    def _act(self):
        d = self.func(*self.args, **self.kwargs)
        d.addCallbacks(self.cbEvent, self.ebEvent)
        for listener in self.listeners:
            d.addBoth(listener.cbListen)
            d.addErrback(listener.ebListen)

        return d

    def start(self):
        self.reactor.callWhenRunning(self._act)

    # ISource

    def addListener(self, listener):
        self.listeners.append(listener)

    def removeListener(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)
            return True
        return False

    def cbEvent(self, data):
        _data = dict()
        _data['action'] = self
        _data['data'] = data
        event = Event('actionDoneEvent', data=_data, key=self.key)
    
        self.log.info("{event!s}", event=event)

        return event

    def ebEvent(self, failure):
        _data = dict()
        _data['failure'] = failure
        _data['action'] = self
        event = Event('actionFailureEvent', data=_data, key=self.key)

        self.log.error("{event!s}", event=event)

        return event


class CycleSource(object):
    log = Logger()
    
    def __init__(self, reactor, func, key=None, limit=0, wait=1, payload=dict()):
        self.running = False
        self.func = func
        self.limit = limit
        self.wait = wait
        self.count = 0
        self.key = key
        self.reactor = reactor
        self.args = payload.get('args', [])
        self.kwargs = payload.get('kwargs', {})
        self.listeners = list()

    def _cbRun(self):
        if self.running:
            d = self.func(*self.args, **self.kwargs)
            d.addCallbacks(self.cbEvent, self.ebEvent)

            for listener in self.listeners:
                d.addBoth(listener.cbListen)
                d.addErrback(listener.ebListen)
            
            wait = 0
            if self.limit > 0:
                self.count += 1
                if self.count % self.limit == 0:
                    self.count = 0
                    wait = self.wait
            
            if wait > 0:
                def _next(ignored):
                    self.reactor.callLater(wait, self._cbRun)
                    return ignored
            else:
                def _next(ignored):
                    self.reactor.callWhenRunning(self._cbRun)
                    return ignored

            d.addBoth(_next)

    def start(self):
        if self.running:
            self.log.info('Cycle is running.')
        else:
            self.running = True
            self.reactor.callWhenRunning(self._cbRun)
    
    def stop(self):
        self.running = False

    # ISource

    def addListener(self, listener):
        self.listeners.append(listener)

    def removeListener(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)
            return True
        return False

    def cbEvent(self, data):
        _data = dict()
        _data['data'] = data
        event = Event('dataRecivedEvent', data=_data, key=self.key)
    
        self.log.info("{event!s}", event=event)

        return event

    def ebEvent(self, failure):
        _data = dict()
        _data['failure'] = failure
        event = Event('dataRecivedFailureEvent', data=_data, key=self.key)

        self.log.error("{event!s}", event=event)

        return event


class LoopSource(object):
    log = Logger()

    def __init__(self, reactor, func, key=None, seconds=1, payload=dict()):
        self.reactor = reactor
        self.func = func
        self.listeners = list()
        self.args = payload.get('args', [])
        self.kwargs = payload.get('kwargs', {})
        self.seconds = seconds
        self.key = key
        self.running = False

    def _run(self):
        if self.running:
            d = task.deferLater(self.reactor, self.seconds, self.func, *self.args, **self.kwargs)
            d.addCallbacks(self.cbEvent, self.ebEvent)

            for listener in self.listeners:
                d.addBoth(listener.cbListen)
                d.addErrback(listener.ebListen)
            def _next(ignored):
                self.reactor.callWhenRunning(self._run)
                return ignored

            d.addBoth(_next)

    def start(self):
        if self.running:
            self.log.info('Loop is running.')
        else:
            self.running = True
            self.reactor.callWhenRunning(self._run)

    def stop(self):
        self.running = False

    # ISource

    def addListener(self, listener):
        self.listeners.append(listener)

    def removeListener(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)
            return True
        return False

    def cbEvent(self, data):
        _data = dict()
        _data['time'] = time.time()
        event = Event('tickEvent', data=_data, key=self.key)
    
        self.log.info("{event!s}", event=event)

        return event

    def ebEvent(self, failure):
        _data = dict()
        _data['failure'] = failure
        event = Event('tickFailureEvent', data=_data, key=self.key)

        self.log.error("{event!s}", event=event)

        return event
    

    

            
