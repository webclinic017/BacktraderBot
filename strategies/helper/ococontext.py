class OcoContext(object):
    def __init__(self):
        self.sl_order = None
        self.tp_order = None

    def reset(self):
        self.sl_order = None
        self.tp_order = None

    def get_sl_order(self):
        return self.sl_order

    def set_sl_order(self, order):
        self.sl_order = order

    def get_tp_order(self):
        return self.tp_order

    def set_tp_order(self, order):
        self.tp_order = order

    def is_sl_order(self, order):
        if order and self.sl_order and order.ref == self.sl_order.ref:
            return True

    def is_tp_order(self, order):
        if order and self.tp_order and order.ref == self.tp_order.ref:
            return True

    def __str__(self):
        sl_order_ref = self.sl_order.ref if self.sl_order else None
        tp_order_ref = self.tp_order.ref if self.tp_order else None
        return "OcoContext <sl_order.ref={}, tp_order.ref={}>".format(sl_order_ref, tp_order_ref)
