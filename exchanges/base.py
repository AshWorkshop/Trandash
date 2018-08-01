class ExchangeService(object):

    def __init__(self, url, accessKey, secretKey):
        self.__url = url
        self.__accessKey = accessKey
        self.__secretKey = secretKey

    def getSymbol(self, pairs):
        pass

    def getOrderBook(self, pairs):
        pass
