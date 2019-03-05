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

    def __init__(self, groupby_list, main_filter, alternative_filter):
        super().__init__()
        self.groupby_list = groupby_list
        self.main_filter = main_filter
        self.alternative_filter = alternative_filter

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
                filtered_df = self.alternative_filter.filter(group_df)
                print("Skipped main filter. Switched to alternative filter, group={}:\nNumber of best rows: {}\n".format(name, len(filtered_df)))
                results_df = self.merge_dataframes(results_df, filtered_df)

        return results_df


class GroupByCombinationsFilter(Filter):

    def __init__(self, groupby_list, group_sortby_variations, sequence_sort_desc_variations):
        super().__init__()
        self.groupby_list = groupby_list
        self.group_sortby_variations = group_sortby_variations
        self.sequence_sort_desc_variations = sequence_sort_desc_variations

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

    def calc_variation(self, grouped_df, group_sortby, sequence_sort_desc):
        result_arr = []
        sorted_groups_arr = []
        for name, group_df in grouped_df:
            group_sorted = group_df.sort_values(by=group_sortby, ascending=False)
            sorted_groups_arr.append(group_sorted)

        sequence_df_arr = sorted(sorted_groups_arr, key=lambda x: x.head(1)[group_sortby].values[0], reverse=sequence_sort_desc)

        selected_strategies_arr = []
        selected_currencypairs_arr = []
        for sequence_df in sequence_df_arr:
            sequence_df_copy = sequence_df.copy().reset_index(drop=False)
            for index, row in sequence_df_copy.iterrows():
                strategy = row["Strategy ID"]
                currency_pair = row["Currency Pair"]
                if self.get_value_index(selected_strategies_arr, strategy) is None and self.get_value_index(selected_currencypairs_arr, currency_pair) is None:
                    selected_strategies_arr.append(strategy)
                    selected_currencypairs_arr.append(currency_pair)
                    result_arr.append(row)
                    break

        result_pd = pd.DataFrame(result_arr)
        return result_pd.sort_values(by='Strategy ID', ascending=True)

    def get_variation_key_str(self, row):
        return "- {}-{}-{}-{}, FwTest: Combined Net Profit={}".format(row["Strategy ID"], row["Exchange"], row["Currency Pair"], row["Timeframe"], round(row["FwTest: Combined Net Profit"]))

    def get_best_variation(self, variations):
        variations_dict = {}
        for result_pd in variations:
            sum_val = result_pd[['FwTest: Combined Net Profit']].sum(axis=0).values[0]
            print("----------------------------------------------  Portolio variation: ------------------------------------------------")
            for index, row in result_pd.iterrows():
                print("{}".format(self.get_variation_key_str(row)))
            print("Sum={}\n".format(round(sum_val)))
            variations_dict[sum_val] = result_pd

        sorted_arr = sorted(variations_dict.items(), key=lambda x: x[0], reverse=True)
        print("**************************** Selected portfolio variation: Sum={}\n".format(round(sorted_arr[0][0])))
        return sorted_arr[0][1]

    def filter(self, df):
        df_copy = df.copy()
        grouped_df = df_copy.groupby(self.groupby_list)

        variations = []
        for group_sortby_var in self.group_sortby_variations:
            for sequence_sort_desc_var in self.sequence_sort_desc_variations:
                variations.append(self.calc_variation(grouped_df, group_sortby_var, sequence_sort_desc_var))

        result_pd = self.get_best_variation(variations)

        return result_pd
