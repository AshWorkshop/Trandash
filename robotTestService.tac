import os
from twisted.internet import reactor
from twisted.application import service
from robotTest import RobotService

def getService():
    return RobotService()

application = service.Application("Robot")

service = getService()
service.setServiceParent(application)

# use `twistd -noy thisSettingFile.tac` to start the robot
# use `Ctrl + C` to stop robot
