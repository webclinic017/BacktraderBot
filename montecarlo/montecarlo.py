import pandas as pd

DEFAULT_SIMS_NUMBER = 10000
DEFAULT_RUIN_VALUE_PCT = 5


class MonteCarloSimulation(object):
    def __init__(self, risk_of_ruin, median_dd, median_profit, median_return, return_to_dd):
        self.risk_of_ruin = risk_of_ruin
        self.median_dd = median_dd
        self.median_profit = median_profit
        self.median_return = median_return
        self.return_to_dd = return_to_dd


class MonteCarloSimulator(object):

    def __init__(self):
        None

    def calculate(self, series, startcash):

        if not isinstance(series, pd.Series):
            raise ValueError("Data must be a Pandas Series")

        results = [series.values]
        for i in range(1, DEFAULT_SIMS_NUMBER):
            results.append(series.sample(frac=1).values)

        df = pd.DataFrame(results).T
        df.rename(columns={0: 'original'}, inplace=True)

        cumsum = df.cumsum()
        total = cumsum[-1:].T
        dd = cumsum.min()[cumsum.min() < 0]
        ruin_value = startcash * DEFAULT_RUIN_VALUE_PCT / 100.0
        total_median = total.median().values[0]
        dd_median = dd.median()

        risk_of_ruin = len(dd[dd <= -ruin_value]) / DEFAULT_SIMS_NUMBER
        median_dd = dd_median / startcash
        median_profit = total_median
        median_return = total_median / startcash
        return_to_dd = abs(median_return / median_dd)

        return MonteCarloSimulation(risk_of_ruin, median_dd, median_profit, median_return, return_to_dd)

