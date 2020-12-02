from datetime import timedelta
from datetime import datetime

from model.common import WFOCycleInfo


class WFOHelper(object):

    def __init__(self):
        pass

    @staticmethod
    def get_wfo_cycles(start_date, num_wfo_cycles, wfo_training_period, wfo_testing_period):
        wfo_cycles = []
        for cycle in range(1, num_wfo_cycles + 1):
            training_start_date = start_date + timedelta(days=(cycle - 1) * wfo_testing_period)
            training_end_date = training_start_date + timedelta(days=wfo_training_period - 1)
            testing_start_date = training_end_date + timedelta(days=1)
            testing_end_date = testing_start_date + timedelta(days=wfo_testing_period - 1)

            if testing_end_date > datetime.now():
                raise Exception("Wrong WFO parameters provided - resulting training/testing period date is in the future: {}".format(testing_end_date))

            wfo_cycles.append(WFOCycleInfo(cycle, wfo_training_period, wfo_testing_period, training_start_date, training_end_date, testing_start_date, testing_end_date))
        return wfo_cycles


    @staticmethod
    def getdaterange(date1, date2):
        return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(date1.year, date1.month, date1.day, date2.year, date2.month, date2.day)
