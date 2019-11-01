
class TrailingBuyManager(object):

    def __init__(self, strategy, oco_context):
        self.strategy = strategy
        self.oco_context = oco_context
        self.broker = strategy.broker
        self.data = strategy.data
