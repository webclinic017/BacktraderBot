
class TrailingBuyManager(object):

    def __init__(self, strategy, strategyprocessor, debug):
        self.strategy = strategy
        self.strategyprocessor = strategyprocessor
        self.broker = strategy.broker
        self.data = strategy.data
        self.debug = debug