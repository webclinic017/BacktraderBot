from datetime import datetime
import os
from pathlib import Path
import random
import uuid
import io

TOKEN001_STR = "{{TOKEN001}}"
TOKEN002_STR = "{{TOKEN002}}"
TOKEN003_STR = "{{TOKEN003}}"
TOKEN004_STR = "{{TOKEN004}}"
TOKEN005_STR = "{{TOKEN005}}"
TOKEN006_STR = "{{TOKEN006}}"
TOKEN007_STR = "{{TOKEN007}}"
TOKEN008_STR = "{{TOKEN008}}"
TOKEN009_STR = "{{TOKEN009}}"
TOKEN010_STR = "{{TOKEN010}}"
TOKEN011_STR = "{{TOKEN011}}"
TOKEN012_STR = "{{TOKEN012}}"
TOKEN_STRATEGY_LIST_STR = "{{STRATEGY_LIST}}"
TOKEN_ADD_STRATEGIES_STR = "{{ADD_STRATEGIES}}"


class TemplateTokensVO(object):
    def __init__(self):
        self.symbol_name = None
        self.shot_type = None
        self.mshot_price_min = None
        self.mshot_price = None
        self.distance = None
        self.buffer = None
        self.tp = None
        self.sl = None

    @classmethod
    def from_pnl_row(cls, is_moonbot, pnl_row):
        obj = cls()
        obj.symbol_name = pnl_row['symbol_name']
        obj.shot_type = pnl_row['shot_type']
        if is_moonbot:
            obj.mshot_price_min = pnl_row['MShotPriceMin']
            obj.mshot_price = pnl_row['MShotPrice']
        else:
            obj.distance = pnl_row['Distance']
            obj.buffer = pnl_row['Buffer']
        obj.tp = pnl_row['TP']
        obj.sl = pnl_row['SL']
        return obj


class ShotStrategyGenerator(object):
    def __init__(self):
        pass

    def whereAmI(self):
        return os.path.dirname(os.path.realpath(__import__("__main__").__file__))

    def get_symbol_type_str(self, is_future):
        if is_future:
            return "future"
        else:
            return "spot"

    def get_app_suffix_str(self, is_moonbot):
        if is_moonbot:
            return "mb"
        else:
            return "mt"

    def read_file(self, filename):
        return Path(filename).read_text()

    def write_file(self, filename, data):
        with io.open(filename, 'w', newline='\r\n') as f:
            f.write(data)

    def get_tokens(self, is_moonbot, is_future, tokens_vo, order_size, extra_desc_info=None):
        symbol_name = tokens_vo.symbol_name
        symbol_type_str = self.get_symbol_type_str(is_future).upper()
        shot_type = tokens_vo.shot_type
        tp = tokens_vo.tp
        sl = tokens_vo.sl
        if is_moonbot:
            extra_suffix = " {} ".format(extra_desc_info) if extra_desc_info else " "
            mshot_price_min = tokens_vo.mshot_price_min
            mshot_price = tokens_vo.mshot_price
            return {
                TOKEN001_STR: "Moonshot [{}]{}{} {} {}-{}-{}-{}".format(symbol_type_str, extra_suffix, symbol_name, shot_type, mshot_price_min, mshot_price, tp, sl),
                TOKEN002_STR: symbol_name,
                TOKEN003_STR: "{:.4f}".format(tp),
                TOKEN004_STR: "{:.8f}".format(sl),
                TOKEN005_STR: "{:.4f}".format(mshot_price_min),
                TOKEN006_STR: "{:.4f}".format(mshot_price),
                TOKEN007_STR: "{}".format(order_size)
            }
        else:
            extra_suffix = " {} ".format(extra_desc_info) if extra_desc_info else " "
            distance = tokens_vo.distance
            buffer = tokens_vo.buffer
            side = 1 if shot_type == "LONG" else -1 if shot_type == "SHORT" else ""
            market_type = 1 if not is_future else 3
            trade_latency = 1.5 if not is_future else 1.5
            strategy_id = int(datetime.now().timestamp() * 1000) + random.randrange(1000000) - random.randrange(100000) + (uuid.uuid1().int % 100000)
            follow_price_delay = 0 if is_future else 0
            return {
                TOKEN001_STR: "{}".format(strategy_id),
                TOKEN002_STR: "Shot [{}]{}{} {} {}-{}-{}-{}".format(symbol_type_str, extra_suffix, symbol_name, shot_type, distance, buffer, tp, sl),
                TOKEN003_STR: symbol_name,
                TOKEN004_STR: "{}".format(distance),
                TOKEN005_STR: "{}".format(buffer),
                TOKEN006_STR: "{}".format(side),
                TOKEN007_STR: "{}".format(order_size),
                TOKEN008_STR: "{}".format(tp),
                TOKEN009_STR: "{}".format(sl),
                TOKEN010_STR: "{}".format(market_type),
                TOKEN011_STR: "{}".format(trade_latency),
                TOKEN012_STR: "{}".format(follow_price_delay)
            }

    def get_template_token_map(self, strategy_list_str, add_strat_template_str):
        return {
            TOKEN_STRATEGY_LIST_STR: strategy_list_str,
            TOKEN_ADD_STRATEGIES_STR: add_strat_template_str
        }

    def apply_template_tokens(self, strategy_template, tokens_map):
        s = strategy_template
        for token, value in tokens_map.items():
            s = s.replace(token, value)
        return s

    def append_divider(self, is_moonbot, strategy_str, is_last):
        if not is_moonbot:
            if not is_last:
                divider = ",\n"
            else:
                divider = ""
            strategy_str = strategy_str + divider
        return strategy_str

    def adjust_tokens_grid(self, is_moonbot, tokens_vo, grid_order_idx, grid_step_pct):
        adjust_distance_val = grid_order_idx * grid_step_pct
        if is_moonbot:
            tokens_vo.mshot_price_min = round(tokens_vo.mshot_price_min + adjust_distance_val, 2)
            tokens_vo.mshot_price = round(tokens_vo.mshot_price + adjust_distance_val, 2)
        else:
            tokens_vo.distance = round(tokens_vo.distance + adjust_distance_val, 2)
        return tokens_vo

    def get_template_filename(self, is_moonbot):
        dirname = self.whereAmI()
        app_suffix_str = self.get_app_suffix_str(is_moonbot)
        return '{}/templates/{}/tmpl.txt'.format(dirname, app_suffix_str)

    def get_strategy_template_filename(self, is_moonbot):
        dirname = self.whereAmI()
        app_suffix_str = self.get_app_suffix_str(is_moonbot)
        return '{}/templates/{}/strat_tmpl.txt'.format(dirname, app_suffix_str)

    def get_add_strategies_template_filename(self, is_moonbot):
        dirname = self.whereAmI()
        app_suffix_str = self.get_app_suffix_str(is_moonbot)
        return '{}/templates/{}/add_strat_tmpl.txt'.format(dirname, app_suffix_str)

    def read_template(self, is_moonbot):
        return self.read_file(self.get_template_filename(is_moonbot))

    def read_strategy_template(self, is_moonbot):
        return self.read_file(self.get_strategy_template_filename(is_moonbot))

    def read_add_strategies_template(self, is_moonbot):
        return self.read_file(self.get_add_strategies_template_filename(is_moonbot))

    def generate_strategy(self, is_moonbot, is_future, strategy_template, tokens_vo, order_size, is_last, extra_desc_info=None):
        tokens_map = self.get_tokens(is_moonbot, is_future, tokens_vo, order_size, extra_desc_info)
        strategy_str = self.apply_template_tokens(strategy_template, tokens_map)
        return self.append_divider(is_moonbot, strategy_str, is_last)

    def generate_final_content(self, strategy_list_str, is_moonbot, is_future):
        template = self.read_template(is_moonbot)
        if not is_moonbot and not is_future:
            add_strat_template_str = self.read_add_strategies_template(is_moonbot)
            return self.apply_template_tokens(template, self.get_template_token_map(strategy_list_str, add_strat_template_str))
        else:
            return self.apply_template_tokens(template, self.get_template_token_map(strategy_list_str, ""))
