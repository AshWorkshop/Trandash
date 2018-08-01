class GateIO:
    def __init__(self, url, apiKey, secretKey):
        self.__url = url
        self.__apiKey = apiKey
        self.__secretKey = secretKey

    def getOrderBooks(self):
        URL = "/api2/1/orderBooks"
        
