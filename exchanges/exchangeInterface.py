from exchanges.base import ExchangeService

class ExchangeInterface(ExchangeService):

    def __init__(self, url, accessKey, secretKey):
        """
        :param url: url of exchange
        :param accessKey: 
        :param secretKey:
        """
        pass

    def getSymbol(self, pairs: ('coin1', 'coin2')) -> str:
        """function to calculate the code of currency pairs
        
        :param pairs: tuple consisting of 2 str, each str stands for a currency
        
        :return: str stand for the currency pairs.
                 `None` if errors occur
        """
        pass

    def getOrderBook(self, pairs: ('coin1', 'coin2')) -> 'orderBook data':
        """query order book info
        :param pairs: tuple consisting of 2 str, each str stands for a currency

        :return: [
                     [[bidPrice, bidAmount], ...],
                     [[askPrice, askAmount], ...]
                 ]
                 note that the price and amount are `float`
                 `None` if errors occur
        """
        pass

    def getBalance(self, coin: str) -> float:
        """query balance of specific currency
        :param coin: str, code stands for currency
        
        :return: float, amount of the specific currency in account
                 `None` if errors occur
        """
        pass

    def getBalances(self, coins: ['coin']) -> 'balances data':
        """query balances of multiple currencies
        :param coins: [coin1, coin2, ...], code of all the currencies to be queried

        :return: {
                     'coin1': coin1Amount,
                     'coin2': coin2Amount,
                     ...
                 }
                 note that the amount are `float`
                 `None` if errors occur
        """
        pass

    def buy(self, pairs, price, amount) -> 'order id':
        """make a buy order
        :param pairs:  tuple consisting of 2 str, each str stands for a currency
        :param price:  float
        :param amount: float
        
        :return: int, the order id of the buy order you made
                 `None` if errors occur
        """
        pass

    def sell(self, pairs, price, amount):
        """make a sell order
        :param pairs:  tuple consisting of 2 str, each str stands for a currency
        :param price:  float
        :param amount: float
        
        :return: int, the order id of the sell order you made
                 `None` if errors occur
        """
        pass

    def getOrder(self, pairs, orderId):
        """query the order with the specific order id
        :param pairs:   tuple consisting of 2 str, each str stands for a currency
        :param orderId: int, order id
        
        :return: {
                     'orderId': orderId,
                     'type': type,
                     'initPrice': initPrice,
                     'initAmount': initAmount,
                     'coinPair': coinPair,
                     'status': status
                 }
                 orderId  : int
                 type     : one of 'buy' or 'sell'
                 initPrice: float
                 coinPair : tuple consisting of 2 str, stands for the pair
                 status   : one of 'open', 'done', 'cancel' or 'error'
                 
                 `None` if errors occur
        """
        pass

    def cancel(self, pairs, orderId):
        """cancel the order with the specific order id
        :param pairs:   tuple consisting of 2 str, each str stands for a currency
        :param orderId: int, order id
        
        :return: True  if succeeded,
                 False if failed
        """
        pass

    def getOrderHistory(self, pairs):
        """query all orders data
        :param pairs:   tuple consisting of 2 str, each str stands for a currency
        
        :return: [
                     {
                         'orderId': orderId,
                         'type': type,
                         'initPrice': initPrice,
                         'initAmount': initAmount,
                         'coinPair': coinPair,
                         'status': status
                     },
                 ...
                 ]
                 orderId  : int
                 type     : one of 'buy' or 'sell'
                 initPrice: float
                 coinPair : tuple consisting of 2 str, stands for the pair
                 status   : one of 'open', 'done', 'cancel' or 'error'
                 
                 `None` if errors occur
        """
        pass

