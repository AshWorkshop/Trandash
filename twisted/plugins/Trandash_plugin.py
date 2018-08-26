from zope.interface import implementer

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet

from robotTest import RobotService

class Options(usage.Options):
    optParameters = [["exchange", "e", "huobipro bitfinex sixty", "The exchanges which robot working on."]] # a test command option, does not work actually

@implementer(IServiceMaker, IPlugin)
class RobotServiceMaker(object):
    tapname = "robot"
    description = ""
    options = Options

    def makeService(self, options):
        return RobotService()

serviceMaker = RobotServiceMaker()
