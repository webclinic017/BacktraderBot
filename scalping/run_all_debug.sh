#! /bin/bash

declare -a symbol_list=("1INCHUSDT" "AAVEUSDT" "ACMUSDT" "ADAUSDT" "AIONUSDT" "AKROUSDT" "ALGOUSDT" "ALICEUSDT" "ALPHAUSDT" "ANKRUSDT" "ARUSDT" "ASRUSDT" "ATMUSDT" "ATOMUSDT" "AUDIOUSDT" "AVAXUSDT" "AXSUSDT" "BAKEUSDT" "BALUSDT" "BANDUSDT" "BARUSDT" "BATUSDT" "BCHUSDT" "BEAMUSDT" "BELUSDT" "BLZUSDT" "BTTUSDT" "BURGERUSDT" "BZRXUSDT" "CAKEUSDT" "CELOUSDT" "CELRUSDT" "CHZUSDT" "CKBUSDT" "COMPUSDT" "COTIUSDT" "CRVUSDT" "CTKUSDT" "CTSIUSDT" "CVCUSDT" "DASHUSDT" "DEGOUSDT" "DENTUSDT" "DGBUSDT" "DIAUSDT" "DODOUSDT" "DOGEUSDT" "DOTUSDT" "EGLDUSDT" "ENJUSDT" "EOSUSDT" "EPSUSDT" "ETCUSDT" "FETUSDT" "FILUSDT" "FLMUSDT" "FTMUSDT" "FTTUSDT" "GRTUSDT" "GXSUSDT" "HARDUSDT" "HBARUSDT" "HOTUSDT" "ICPUSDT" "ICXUSDT" "INJUSDT" "IOSTUSDT" "IOTAUSDT" "IOTXUSDT" "IRISUSDT" "JUVUSDT" "KAVAUSDT" "KNCUSDT" "KSMUSDT" "LINAUSDT" "LINKUSDT" "LITUSDT" "LRCUSDT" "LSKUSDT" "LUNAUSDT" "MANAUSDT" "MATICUSDT" "MFTUSDT" "MITHUSDT" "MKRUSDT" "NANOUSDT" "NEARUSDT" "NEOUSDT" "NKNUSDT" "OCEANUSDT" "OGNUSDT" "OGUSDT" "OMGUSDT" "OMUSDT" "ONEUSDT" "ONTUSDT" "OXTUSDT" "PERPUSDT" "PONDUSDT" "PSGUSDT" "PUNDIXUSDT" "QTUMUSDT" "REEFUSDT" "RENUSDT" "RLCUSDT" "RSRUSDT" "RUNEUSDT" "RVNUSDT" "SANDUSDT" "SCUSDT" "SFPUSDT" "SHIBUSDT" "SKLUSDT" "SLPUSDT" "SNXUSDT" "SOLUSDT" "SRMUSDT" "STMXUSDT" "STORJUSDT" "STRAXUSDT" "SUSHIUSDT" "SXPUSDT" "TFUELUSDT" "THETAUSDT" "TKOUSDT" "TLMUSDT" "TOMOUSDT" "TRBUSDT" "TRXUSDT" "TWTUSDT" "UNFIUSDT" "UNIUSDT" "UTKUSDT" "VETUSDT" "VITEUSDT" "VTHOUSDT" "WAVESUSDT" "WINUSDT" "WRXUSDT" "WTCUSDT" "XEMUSDT" "XLMUSDT" "XMRUSDT" "XRPUSDT" "XTZUSDT" "XVSUSDT" "YFIIUSDT" "YFIUSDT" "ZECUSDT" "ZENUSDT" "ZILUSDT" "ZRXUSDT")

declare -a start_minutes_ago=30

declare -a future_flag=""

declare -a moonbot_flag=""

declare -a order_size_mb=0.0002
declare -a order_size_mt=100

now_timestamp="$(date +'%s')"
now_timestamp=$((now_timestamp - now_timestamp % 60))

start_timestamp=$((now_timestamp - 60 * start_minutes_ago))
start_date="$(date -j -f "%s" "${start_timestamp}" "+%Y-%m-%dT%H:%M:%S")"
end_timestamp=$((start_timestamp + 60 * start_minutes_ago))
end_date="$(date -j -f "%s" "${end_timestamp}" "+%Y-%m-%dT%H:%M:%S")"

output_folder_prefix="$(date -j -f "%s" "${end_timestamp}" "+%Y%m%d_%H%M")"
output_folder="/Users/alex/Cloud@Mail.Ru/_TEMP/scalping/out/strategies/${output_folder_prefix}/"

if [ -d "/opt/anaconda3" ]; then
    source /opt/anaconda3/etc/profile.d/conda.sh
elif [ -d "/home/alex/anaconda3" ]; then
    source /home/alex/anaconda3/etc/profile.d/conda.sh
elif [ -d "/Users/alex/anaconda3" ]; then
    source /Users/alex/anaconda3/etc/profile.d/conda.sh
fi
conda activate Backtrader

# Generate strategy files for MB/MT
python strategy_generator.py -e binance -t $order_size_mb -y $order_size_mt $future_flag $moonbot_flag
