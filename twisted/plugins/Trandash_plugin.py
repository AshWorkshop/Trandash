from zope.interface import implementer

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.logger import Logger, ILogObserver, formatEvent, globalLogPublisher
from twisted.application.service import IServiceMaker
from twisted.application import internet

from robotTest import RobotService

class Options(usage.Options):
    optParameters = [["exchanges", "e", "huobipro bitfinex sixty", "The exchanges which robot working on."]] # a test command option, does not work actually

    def postOptions(self):
        pass

@implementer(IServiceMaker, IPlugin)
class RobotServiceMaker(object):
    tapname = "robot"
    description = ""
    options = Options

    def makeService(self, options):
        return RobotService()

serviceMaker = RobotServiceMaker()
