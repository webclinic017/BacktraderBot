from strategies.helper.constants import TradeExitMode


class ParametersValidator(object):

    @classmethod
    def validate_params(cls, params):
        if not params.get("needlong") and not params.get("needshort"):
            raise ValueError("Either 'needlong' or 'needshort' parameters must be provided")
        if not params.get("exitmode"):
            raise ValueError("The 'exitmode' parameter must be provided")
        if params.get("exitmode") and params.get("exitmode") != TradeExitMode.EXIT_MODE_DEFAULT and params.get("exitmode") != TradeExitMode.EXIT_MODE_SET_DYNAMIC_SLTP_WITH_ATR:
            raise ValueError("The 'exitmode' parameter should be set to {}, or {}".format(TradeExitMode.EXIT_MODE_DEFAULT, TradeExitMode.EXIT_MODE_SET_DYNAMIC_SLTP_WITH_ATR))
        if params.get("tslflag") and not params.get("sl"):
            raise ValueError("The TRAILING STOP-LOSS ('tslflag') parameter should be provided with STOP-LOSS ('sl') parameter")
        if params.get("ttpdist") and not params.get("tp"):
            raise ValueError("The TRAILING TAKE-PROFIT ('ttpdist') parameter cannot be provided without TAKE-PROFIT ('tp') parameter")
        if params.get("dcainterval") and not params.get("numdca") or not params.get("dcainterval") and params.get("numdca"):
            raise ValueError("Both DCA-MODE parameters 'dcainterval' and 'numdca' must be provided")
        if params.get("numdca") and params.get("numdca") < 2:
            raise ValueError("The DCA-MODE parameters 'dcainterval' must greater or equal 2")
        if params.get("dcainterval") and params.get("numdca") and params.get("tbdist"):
            raise ValueError("Both TRAILING-BUY ('tbdist') and DCA-MODE ('dcainterval'/'numdca') parameters can not be used together: only one mode (TRAILING-BUY or DCA-MODE) can be used at the same time")
        if params.get("dcainterval") and params.get("numdca") and (params.get("tslflag") or params.get("ttpdist")):
            raise ValueError("The DCA-MODE ('dcainterval'/'numdca') parameters cannot be configured together with TRAILING STOP-LOSS ('tslflag') or TRAILING TAKE-PROFIT ('ttpdist') parameters. Only STOP-LOSS ('sl') and TAKE-PROFIT ('tp') parameters allowed")
        if params.get("dcainterval") and params.get("numdca") and not params.get("tp"):
            raise ValueError("The DCA-MODE ('dcainterval'/'numdca') parameters must be configured together with TAKE-PROFIT ('tp') parameter")
        return True
