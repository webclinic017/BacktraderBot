class StFetcher(object):
    _STRATS = []

    @classmethod
    def cleanall(cls, ):
        cls._STRATS = []

    @classmethod
    def register(cls, target, *args, **kwargs):
        cls._STRATS.append([target, args, kwargs])

    @classmethod
    def COUNT(cls):
        return range(len(cls._STRATS))

    def __new__(cls, *args, **kwargs):
        idx = kwargs.pop('idx')
        kwargs_arr = cls._STRATS[idx][2]
        obj = cls._STRATS[idx][0](*args, **kwargs_arr)
        return obj