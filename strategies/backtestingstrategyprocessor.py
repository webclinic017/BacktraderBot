
class BacktestingStrategyProcessor(object):

    def __init__(self, strategy, debug):
        self.strategy = strategy
        self.broker = strategy.broker
        self.analyzers = strategy.analyzers
        self.data = strategy.data
        self.debug = debug

    def set_startcash(self, startcash):
        self.broker.setcash(startcash)
        # TODO: Workaround
        self.analyzers.dd.p.initial_cash = startcash
        self.analyzers.dd.maxportfoliovalue = startcash
        self.analyzers.ta.p.cash = startcash

    def log(self, txt, dt=None):
        if self.p.debug:
            dt = dt or self.data.datetime.datetime()
            print('%s  %s' % (dt, txt))

    def notify_data(self, data, status, *args, **kwargs):
        pass

    def buy(self):
        self.strategy.buy(tradeid=self.strategy.curtradeid)

    def sell(self):
        self.strategy.sell(tradeid=self.strategy.curtradeid)

    def close(self):
        self.strategy.close(tradeid=self.strategy.curtradeid)
