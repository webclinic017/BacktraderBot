from common.constants import *
import backtrader as bt


class BrokerMappings(object):

    _CONFIG = {
        BINANCE_EXCHANGE: {
        },
        BITFINEX_EXCHANGE: {
            'order_types': {
                bt.Order.Market: 'market',
                bt.Order.Limit: 'limit',
                bt.Order.Stop: 'stop-loss',
                bt.Order.StopLimit: 'stop limit'
            },
            'mappings': {
                'closed_order': {
                    'key': 'status',
                    'value': 'closed'
                },
                'canceled_order': {
                    'key': 'status',
                    'value': 'canceled'
                }
            }
        }
    }

    @classmethod
    def get_broker_mapping(cls, exchange):
        return cls._CONFIG.get(exchange)
