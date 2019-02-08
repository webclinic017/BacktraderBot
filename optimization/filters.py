
class Filter(object):
    def __init__(self):
        pass


class ValueFilter(Filter):
    field_name = None

    value = None

    is_below = None

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


class TopNPercentFilter(Filter):
    field_name = None
    percent = None
    ascending = None

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


class CombinedResultsMergingFilter(Filter):

    _filters = []

    def __init__(self, filters):
        super().__init__()
        self._filters = filters

    def get_value_by_idx(self, df, idx):
        try:
            result = df.loc[[idx]]
        except KeyError:
            result = None
        return result

    def merge_dataframes(self, target_df, src_df):
        result = None
        if src_df is not None:
            if target_df is None:
                result = src_df.copy()
            else:
                for src_idx, src_row in src_df.iterrows():
                    row = self.get_value_by_idx(target_df, src_idx)
                    if row is None or len(row) == 0:
                        target_df.loc[src_idx] = src_row
                result = target_df

        return result

    def filter(self, df):
        results_df = None
        for f in self._filters:
            data_filtered = f.filter(df)
            results_df = self.merge_dataframes(results_df, data_filtered)
        return results_df


class FilterSequence(Filter):

    _filters = []

    def __init__(self, filters):
        super().__init__()
        self._filters = filters

    def filter(self, df):
        process_df = df
        for f in self._filters:
            process_df = f.filter(process_df)
        return process_df
