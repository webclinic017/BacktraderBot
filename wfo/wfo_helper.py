from datetime import timedelta
from datetime import datetime


class WFOCycleInfo(object):
    def __init__(self, wfo_cycle, training_start_date, training_end_date, test_start_date, test_end_date):
        self.wfo_cycle = wfo_cycle
        self.training_start_date = training_start_date
        self.training_end_date = training_end_date
        self.test_start_date = test_start_date
        self.test_end_date = test_end_date


class WFOHelper(object):

    def __init__(self):
        pass


    @staticmethod
    def get_wfo_cycles(start_date, num_wfo_cycles, training_period, test_period):
        wfo_cycles = []
        for cycle in range(1, num_wfo_cycles + 1):
            training_start_date = start_date + timedelta(days=(cycle - 1) * test_period)
            training_end_date = training_start_date + timedelta(days=training_period - 1)
            test_start_date = training_end_date + timedelta(days=1)
            test_end_date = test_start_date + timedelta(days=test_period - 1)

            if test_end_date > datetime.now():
                raise Exception("Wrong WFO parameters provided - resulting training/test period date is in the future: {}".format(test_end_date))

            wfo_cycles.append(WFOCycleInfo(cycle, training_start_date, training_end_date, test_start_date, test_end_date))
        return wfo_cycles
