#! /bin/bash

declare -a symbol_list=("1INCHUSDT" "AAVEUSDT" "ADAUSDT" "AKROUSDT" "ALGOUSDT" "ALICEUSDT" "ALPHAUSDT" "ANKRUSDT" "ATOMUSDT" "AVAXUSDT" "AXSUSDT" "BALUSDT" "BANDUSDT" "BATUSDT" "BCHUSDT" "BELUSDT" "BLZUSDT" "BTSUSDT" "BZRXUSDT" "CHRUSDT" "CHZUSDT" "COMPUSDT" "COTIUSDT" "CRVUSDT" "CTKUSDT" "CVCUSDT" "DASHUSDT" "DODOUSDT" "DOGEUSDT" "DOTUSDT" "EGLDUSDT" "ENJUSDT" "EOSUSDT" "ETCUSDT" "FILUSDT" "FLMUSDT" "FTMUSDT" "GRTUSDT" "HBARUSDT" "HNTUSDT" "ICXUSDT" "IOSTUSDT" "IOTAUSDT" "KAVAUSDT" "KNCUSDT" "KSMUSDT" "LINKUSDT" "LITUSDT" "LRCUSDT" "LUNAUSDT" "MANAUSDT" "MATICUSDT" "MKRUSDT" "NEARUSDT" "NEOUSDT" "OCEANUSDT" "OMGUSDT" "ONEUSDT" "ONTUSDT" "QTUMUSDT" "REEFUSDT" "RENUSDT" "RLCUSDT" "RSRUSDT" "RUNEUSDT" "RVNUSDT" "SANDUSDT" "SFPUSDT" "SKLUSDT" "SNXUSDT" "SOLUSDT" "SRMUSDT" "STMXUSDT" "STORJUSDT" "SUSHIUSDT" "SXPUSDT" "THETAUSDT" "TOMOUSDT" "TRBUSDT" "TRXUSDT" "UNFIUSDT" "UNIUSDT" "VETUSDT" "WAVESUSDT" "XEMUSDT" "XLMUSDT" "XMRUSDT" "XRPUSDT" "XTZUSDT" "YFIIUSDT" "YFIUSDT" "ZECUSDT" "ZENUSDT" "ZILUSDT" "ZRXUSDT")

declare -a start_hours_ago=2

declare -a future_flag="-f"

declare -a moonbot_flag=""

declare -a order_size_mb=0.0002
declare -a order_size_mt=200


if [ -d "/opt/anaconda3" ]; then
    source /opt/anaconda3/etc/profile.d/conda.sh
elif [ -d "/home/alex/anaconda3" ]; then
    source /home/alex/anaconda3/etc/profile.d/conda.sh
elif [ -d "/Users/alex/anaconda3" ]; then
    source /Users/alex/anaconda3/etc/profile.d/conda.sh
fi
conda activate Backtrader

# Calculate best PnL for all the shots
for symbol in "${symbol_list[@]}"
do
    python calc_shots_pnl.py -e binance -s $symbol $future_flag $moonbot_flag
done
