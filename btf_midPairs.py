hasList = ['ltcbtc', 'ethbtc', 'etcbtc', 'rrtbtc', 'zecbtc', 'xmrbtc', 'dshbtc',
 'xrpbtc', 'iotbtc', 'ioteth', 'eosbtc', 'eoseth', 'sanbtc', 'saneth', 'omgbtc', 
 'omgeth', 'bchbtc', 'bcheth', 'neobtc', 'neoeth', 'etpbtc', 'etpeth', 'qtmbtc', 
 'qtmeth', 'avtbtc', 'avteth', 'edobtc', 'edoeth', 'btgbtc', 'datbtc', 'dateth', 
 'qshbtc', 'qsheth', 'yywbtc', 'yyweth', 'gntbtc', 'gnteth', 'sntbtc', 'snteth', 
 'batbtc', 'bateth', 'mnabtc', 'mnaeth', 'funbtc', 'funeth', 'zrxbtc', 'zrxeth', 
 'tnbbtc', 'tnbeth', 'spkbtc', 'spketh', 'trxbtc', 'trxeth', 'rcnbtc', 'rcneth', 
 'rlcbtc', 'rlceth', 'aidbtc', 'aideth', 'sngbtc', 'sngeth', 'repbtc', 'repeth', 
 'elfbtc', 'elfeth', 'iosbtc', 'ioseth', 'aiobtc', 'aioeth', 'reqbtc', 'reqeth', 
 'rdnbtc', 'rdneth', 'lrcbtc', 'lrceth', 'waxbtc', 'waxeth', 'daibtc', 'daieth', 
 'cfibtc', 'cfieth', 'agibtc', 'agieth', 'bftbtc', 'bfteth', 'mtnbtc', 'mtneth', 
 'odebtc', 'odeeth', 'antbtc', 'anteth', 'dthbtc', 'dtheth', 'mitbtc', 'miteth', 
 'stjbtc', 'stjeth', 'xlmbtc', 'xlmeth', 'xvgbtc', 'xvgeth', 'bcibtc', 'mkrbtc', 
 'mkreth', 'venbtc', 'veneth', 'kncbtc', 'knceth', 'poabtc', 'poaeth', 'lymbtc', 
 'lymeth', 'utkbtc', 'utketh', 'veebtc', 'veeeth', 'dadbtc', 'dadeth', 'orsbtc', 
 'orseth', 'aucbtc', 'auceth', 'poybtc', 'poyeth', 'fsnbtc', 'fsneth', 'cbtbtc', 
 'cbteth', 'zcnbtc', 'zcneth', 'senbtc', 'seneth', 'ncabtc', 'ncaeth', 'cndbtc', 
 'cndeth', 'ctxbtc', 'ctxeth', 'paibtc', 'seebtc', 'seeeth', 'essbtc', 'esseth', 
 'atmbtc', 'atmeth', 'hotbtc', 'hoteth', 'dtabtc', 'dtaeth', 'iqxbtc', 'iqxeos', 
 'wprbtc', 'wpreth', 'zilbtc', 'zileth', 'bntbtc', 'bnteth', 'abseth', 'xraeth', 
 'maneth']

midList = ['btc', 'eth', 'eos']

def getPairs():
    '''return : a list of: [coinA, coinB, coinC],...'''
    coinA = 'usd'
    coinPairs = []
    for pair in hasList:
        coinB = pair[:3]
        coinC = pair[3:]
        coinPairs.append([coinA, coinB, coinC])

    return coinPairs