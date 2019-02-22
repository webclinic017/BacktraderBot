
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


class TopNFilter(Filter):
    field_name = None
    number = None
    ascending = None

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
