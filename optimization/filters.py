import pandas as pd

class Filter(object):
    def __init__(self):
        pass


class ValueFilter(Filter):
    def __init__(self, field_name, value, is_below):
        super().__init__()
        self.field_name = field_name
        self.value = value
        self.is_below = is_below

    def filter(self, df):
        result = None
        if df is not None and len(df.index) > 0:
            if self.is_below is True:
                result = df[df[self.field_name] <= self.value]
            else:
                result = df[df[self.field_name] >= self.value]
        return result


class TopNFilter(Filter):
    def __init__(self, field_name, number, ascending):
        super().__init__()
        self.field_name = field_name
        self.number = number
        self.ascending = ascending

    def sort(self, df, fname, asc):
        return df.sort_values(by=fname, ascending=asc)

    def filter(self, df):
        result = None
        if df is not None and len(df.index) > 0:
            df = self.sort(df, self.field_name, self.ascending)

            result = df.head(self.number)

        return result


class TopNPercentFilter(Filter):
    def __init__(self, field_name, percent, ascending):
        super().__init__()
        self.field_name = field_name
        self.percent = percent
        self.ascending = ascending

    def sort(self, df, fname, asc):
        return df.sort_values(by=fname, ascending=asc)

    def get_filter_criterion(self, df, pct, fname, asc):
        result = None
        top_row = df.head(1)
        top_value = top_row[fname].values[0]
        if asc is False:
            result = top_value - abs(top_value * pct / 100)
        else:
            result = top_value + abs(top_value * pct / 100)

        return result

    def filter(self, df):
        result = None
        if df is not None and len(df.index) > 0:
            df = self.sort(df, self.field_name, self.ascending)

            filter_criterion = self.get_filter_criterion(df, self.percent, self.field_name, self.ascending)
            if self.ascending is False:
                result = df[df[self.field_name] >= filter_criterion]
            else:
                result = df[df[self.field_name] <= filter_criterion]

        return result


class FilterSequence(Filter):

    def __init__(self, filters):
        super().__init__()
        self._filters = filters

    def filter(self, df):
        process_df = df
        for f in self._filters:
            process_df = f.filter(process_df)
        return process_df


class GroupByConditionalFilter(Filter):

    def __init__(self, groupby_list, main_filter):
        super().__init__()
        self.groupby_list = groupby_list
        self.main_filter = main_filter

    def merge_dataframes(self, target_df, src_df):
        if target_df is None:
            return src_df
        else:
            return pd.concat([target_df, src_df])

    def filter(self, df):
        results_df = None

        df_copy = df.copy()
        grouped = df_copy.groupby(self.groupby_list)

        for name, group_df in grouped:
            filtered_df = self.main_filter.filter(group_df)
            if filtered_df is not None and len(filtered_df) > 0:
                print("Processing main filter, group={}:\nNumber of best rows: {}\n".format(name, len(filtered_df)))
                results_df = self.merge_dataframes(results_df, filtered_df)
            else:
                print("Skipped main filter, group={}:\n".format(name))

        return results_df


class GroupByCombinationsFilter(Filter):

    def __init__(self, groupby_list, group_sortby_variations):
        super().__init__()
        self.groupby_list = groupby_list
        self.group_sortby_variations = group_sortby_variations

    def merge_dataframes(self, target_df, src_df):
        if target_df is None:
            return src_df
        else:
            return pd.concat([target_df, src_df])

    def get_value_index(self, arr, val):
        try:
            result = arr.index(val)
        except ValueError:
            result = None
        return result

    def get_combination_key_str(self, group_sortby):
        return "group_sortby={}".format(group_sortby)

    def get_combination_str(self, row):
        return "- {}-{}-{}-{}, FwTest: Combined Net Profit={}".format(row["Strategy ID"], row["Exchange"], row["Currency Pair"], row["Timeframe"], round(row["FwTest: Combined Net Profit"]))

    def calc_portfolio_combination(self, grouped_df, group_sortby):
        result_arr = []
        sorted_groups_arr = []
        for name, group_df in grouped_df:
            group_sorted = group_df.sort_values(by=group_sortby, ascending=False)
            sorted_groups_arr.append(group_sorted)

        sequence_df_arr = sorted(sorted_groups_arr, key=lambda x: x.head(1)[group_sortby].values[0], reverse=False)

        selected_strategies_arr = []
        selected_currencypairs_arr = []
        for sequence_df in sequence_df_arr:
            sequence_df_copy = sequence_df.copy().reset_index(drop=False)
            for index, row in sequence_df_copy.iterrows():
                strategy = row["Strategy ID"]
                currency_pair = row["Currency Pair"]
                if self.get_value_index(selected_currencypairs_arr, currency_pair) is None: #and self.get_value_index(selected_strategies_arr, strategy) is None:
                    selected_strategies_arr.append(strategy)
                    selected_currencypairs_arr.append(currency_pair)
                    result_arr.append(row)
                    break

        #if len(selected_currencypairs_arr) < len(sequence_df_arr):  # Skip this combination if number of selected currencies less than the number of original grouped currencies
        #    return []

        result_pd = pd.DataFrame(result_arr)
        result_pd = result_pd.sort_values(by='Strategy ID', ascending=True)

        sum_val = result_pd[['FwTest: Combined Net Profit']].sum(axis=0).values[0]
        combination_key = self.get_combination_key_str(group_sortby)
        print("----------------------------------------------  Portfolio combination: Key: {}  ----------------------".format(combination_key))
        for index, row in result_pd.iterrows():
            print("{}".format(self.get_combination_str(row)))
        print("Portfolio Combined Net Profit={}\n".format(round(sum_val)))

        return [combination_key, sum_val, result_pd]

    def get_best_combination(self, combinations):
        combinations_dict = {}
        for combination in combinations:
            combination_key = combination[0]
            sum_val = combination[1]
            result_pd = combination[2]
            combinations_dict[combination_key] = [sum_val, result_pd]

        sorted_arr = sorted(combinations_dict.items(), key=lambda x: x[1][0], reverse=True)
        print("**************************** Total number of portfolio combinations: {}\n".format(len(sorted_arr)))
        best_combination = sorted_arr[0]
        key = best_combination[0]
        net_profit = round(best_combination[1][0])
        best_result_pd = best_combination[1][1]
        print("**************************** Best portfolio combination: Key: {}, Portfolio Combined Net Profit: {}\n".format(key, net_profit))
        return best_result_pd

    def filter(self, df):
        df_copy = df.copy()
        grouped_df = df_copy.groupby(self.groupby_list)

        combinations = []
        for group_sortby_var in self.group_sortby_variations:
            combination = self.calc_portfolio_combination(grouped_df, group_sortby_var)
            if len(combination) > 0:
                combinations.append(combination)

        result_pd = self.get_best_combination(combinations)

        return result_pd
