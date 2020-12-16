from datetime import timedelta
from datetime import datetime
from model.reports_common import ColumnName
from model.common import WFOCycleInfo, WFOTestingData, WFOTestingDataList


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

            wfo_cycles.append(WFOCycleInfo(cycle, wfo_training_period, wfo_testing_period, training_start_date, training_end_date, testing_start_date, testing_end_date, num_wfo_cycles))
        return wfo_cycles


    @staticmethod
    def getdaterange(date1, date2):
        return "{}{:02d}{:02d}-{}{:02d}{:02d}".format(date1.year, date1.month, date1.day, date2.year, date2.month, date2.day)

    @staticmethod
    def get_unique_index_values(df, name):
        return df.index.get_level_values(name).unique()

    @staticmethod
    def get_unique_index_value_lists(df):
        strat_list = WFOHelper.get_unique_index_values(df, ColumnName.STRATEGY_ID)
        exc_list = WFOHelper.get_unique_index_values(df, ColumnName.EXCHANGE)
        sym_list = WFOHelper.get_unique_index_values(df, ColumnName.CURRENCY_PAIR)
        tf_list = WFOHelper.get_unique_index_values(df, ColumnName.TIMEFRAME)
        return strat_list, exc_list, sym_list, tf_list

    @staticmethod
    def get_processing_daterange(data):
        result = {}

        range_splitted = data.split('-')
        start_date = range_splitted[0]
        end_date = range_splitted[1]
        s = datetime.strptime(start_date, '%Y%m%d')
        e = datetime.strptime(end_date, '%Y%m%d')

        result['fromyear'] = s.year
        result['frommonth'] = s.month
        result['fromday'] = s.day
        result['toyear'] = e.year
        result['tomonth'] = e.month
        result['today'] = e.day
        return result

    @staticmethod
    def get_fromdate(arr):
        fromyear = arr["fromyear"]
        frommonth = arr["frommonth"]
        fromday = arr["fromday"]
        return datetime(fromyear, frommonth, fromday)

    @staticmethod
    def get_todate(arr):
        toyear = arr["toyear"]
        tomonth = arr["tomonth"]
        today = arr["today"]
        return datetime(toyear, tomonth, today)

    @staticmethod
    def parse_wfo_testing_data(df):
        wfo_testing_data_list = WFOTestingDataList()
        strat_list, exc_list, sym_list, tf_list = WFOHelper.get_unique_index_value_lists(df)
        for strategy in strat_list:
            for exchange in exc_list:
                for symbol in sym_list:
                    for timeframe in tf_list:
                        wfo_testing_data = WFOTestingData(strategy, exchange, symbol, timeframe)
                        data_df = df.loc[[(strategy, exchange, symbol, timeframe)]]
                        num_wfo_cycles = data_df[ColumnName.WFO_CYCLE_ID].max()
                        num_trained_params = len(data_df.loc[data_df[ColumnName.WFO_CYCLE_ID] == 1])

                        for wfo_cycle_id in range(1, num_wfo_cycles + 1):
                            wfo_cycle_df = data_df.loc[data_df[ColumnName.WFO_CYCLE_ID] == wfo_cycle_id]
                            cycle_first_row = wfo_cycle_df.iloc[0]
                            wfo_training_period = cycle_first_row[ColumnName.WFO_TRAINING_PERIOD]
                            wfo_testing_period = cycle_first_row[ColumnName.WFO_TESTING_PERIOD]
                            training_daterange = WFOHelper.get_processing_daterange(cycle_first_row[ColumnName.TRAINING_DATE_RANGE])
                            testing_daterange = WFOHelper.get_processing_daterange(cycle_first_row[ColumnName.TESTING_DATE_RANGE])
                            wfo_cycle_info = WFOCycleInfo(wfo_cycle_id,
                                                          wfo_training_period,
                                                          wfo_testing_period,
                                                          WFOHelper.get_fromdate(training_daterange),
                                                          WFOHelper.get_todate(training_daterange),
                                                          WFOHelper.get_fromdate(testing_daterange),
                                                          WFOHelper.get_todate(testing_daterange),
                                                          num_wfo_cycles)
                            wfo_testing_data.set_wfo_cycle(wfo_cycle_info)
                            for wfo_cycle_training_id in range(1, num_trained_params + 1):
                                wfo_trained_data_df = wfo_cycle_df.iloc[wfo_cycle_training_id - 1]
                                if wfo_cycle_training_id in wfo_testing_data.training_id_params_dict:
                                    wfo_cycle_params_dict = wfo_testing_data.training_id_params_dict[wfo_cycle_training_id]
                                else:
                                    wfo_cycle_params_dict = dict()
                                wfo_cycle_params_dict[wfo_cycle_id] = wfo_trained_data_df[ColumnName.PARAMETERS]
                                wfo_testing_data.training_id_params_dict[wfo_cycle_training_id] = wfo_cycle_params_dict

                        wfo_testing_data_list.add_wfo_testing_data(wfo_testing_data)

        return wfo_testing_data_list
