
from common.constants import *

class RateLimitConfig(object):

    _DEFAULT_RATE_LIMIT = 4000

    _CONFIG = {
        BINANCE_EXCHANGE: {
            "fetch_ticker": {
                "base_limit_rate": 100,
                "apply_factor": False
            },
            "get_wallet_balance": {
                "base_limit_rate": 100,
                "apply_factor": False
            },
            "get_balance": {
                "base_limit_rate": 100,
                "apply_factor": False
            },
            "getposition": {
                "base_limit_rate": 100,
                "apply_factor": False
            },
            "create_order": {
                "base_limit_rate": 100,
                "apply_factor": False
            },
            "cancel_order": {
                "base_limit_rate": 100,
                "apply_factor": False
            },
            "fetch_trades": {
                "base_limit_rate": 100,
                "apply_factor": False
            },
            "fetch_my_trades": {
                "base_limit_rate": 100,
                "apply_factor": False
            },
            "fetch_ohlcv": {
                "base_limit_rate": 100,
                "apply_factor": True
            },
            "fetch_order": {
                "base_limit_rate": 100,
                "apply_factor": False
            },
            "fetch_open_orders": {
                "base_limit_rate": 100,
                "apply_factor": False
            },
        },
        BITFINEX_EXCHANGE: {
            "fetch_ticker": {
                "base_limit_rate": 4000,
                "apply_factor": False
            },
            "get_wallet_balance": {
                "base_limit_rate": 4000,
                "apply_factor": False
            },
            "get_balance": {
                "base_limit_rate": 4000,
                "apply_factor": False
            },
            "getposition": {
                "base_limit_rate": 4000,
                "apply_factor": False
            },
            "create_order": {
                "base_limit_rate": 4000,
                "apply_factor": False
            },
            "cancel_order": {
                "base_limit_rate": 4000,
                "apply_factor": False
            },
            "fetch_trades": {
                "base_limit_rate": 4000,
                "apply_factor": False
            },
            "fetch_my_trades": {
                "base_limit_rate": 4000,
                "apply_factor": False
            },
            "fetch_ohlcv": {
                "base_limit_rate": 4000,
                "apply_factor": True
            },
            "fetch_order": {
                "base_limit_rate": 4000,
                "apply_factor": False
            },
            "fetch_open_orders": {
                "base_limit_rate": 4000,
                "apply_factor": False
            },
        }
    }

    @classmethod
    def get_rate_limit(cls, exchange, method_name, factor):
        result = 0
        try:
            exchange = exchange.lower()
            config = cls._CONFIG.get(exchange).get(method_name)
            base_rate_limit = config.get("base_limit_rate")
            result = base_rate_limit
            if config.get("apply_factor") is True:
                result *= factor
            #print("Calculated rate_limit for {} method: {}".format(method_name, result))
        except Exception:
            print("Exception occurred. Reverted to default rate_limit for {} method: {}".format(method_name, result))
            result = cls._DEFAULT_RATE_LIMIT
        return result
