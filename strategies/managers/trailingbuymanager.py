
class TrailingBuyManager(object):

    def __init__(self, strategy, debug):
        self.strategy = strategy
        self.broker = strategy.broker
        self.data = strategy.data
        self.debug = debug