#! /bin/bash

declare -a symbol_list=("DOGEUSDT" "ADAUSDT" "XRPUSDT" "MATICUSDT" "DOTUSDT" "ETCUSDT" "EOSUSDT" "SHIBUSDT" "CHZUSDT" "XLMUSDT" "LINKUSDT" "BCHUSDT" "ATMUSDT" "TRXUSDT" "VETUSDT" "SUSHIUSDT" "RLCUSDT" "AAVEUSDT" "FILUSDT" "ATOMUSDT" "AVAXUSDT" "BAKEUSDT" "NEARUSDT" "SXPUSDT" "KSMUSDT" "ICPUSDT" "UNIUSDT" "ZECUSDT" "ONEUSDT" "CAKEUSDT" "BTTUSDT" "REEFUSDT" "SOLUSDT" "XVSUSDT" "CRVUSDT" "ONTUSDT" "THETAUSDT" "YFIUSDT" "HBARUSDT" "JUVUSDT" "FTMUSDT" "COTIUSDT" "LUNAUSDT" "XMRUSDT" "NEOUSDT" "SNXUSDT" "OMGUSDT" "ALGOUSDT" "NANOUSDT" "GRTUSDT" "PSGUSDT" "QTUMUSDT" "WINUSDT" "ACMUSDT" "GXSUSDT" "DASHUSDT" "BLZUSDT" "CTSIUSDT" "RUNEUSDT" "1INCHUSDT" "HOTUSDT" "DENTUSDT" "XTZUSDT" "RVNUSDT" "WAVESUSDT" "OMUSDT" "ALPHAUSDT" "ZILUSDT" "IOTAUSDT" "TLMUSDT" "EGLDUSDT" "ASRUSDT" "ZENUSDT" "COMPUSDT" "ENJUSDT" "XEMUSDT" "BARUSDT" "ALICEUSDT" "IOSTUSDT" "SANDUSDT" "CELRUSDT" "ICXUSDT" "SLPUSDT" "ARUSDT" "LRCUSDT" "STMXUSDT" "RSRUSDT" "TKOUSDT" "FTTUSDT" "SRMUSDT" "BURGERUSDT" "NKNUSDT" "PERPUSDT" "OGUSDT" "LSKUSDT" "SCUSDT" "BATUSDT" "EPSUSDT" "MKRUSDT" "WRXUSDT" "BANDUSDT" "VITEUSDT" "ANKRUSDT" "TRBUSDT" "HARDUSDT" "OGNUSDT" "LINAUSDT" "AIONUSDT" "RENUSDT" "FLMUSDT" "DGBUSDT" "FETUSDT" "MANAUSDT" "OCEANUSDT" "KAVAUSDT" "INJUSDT" "LITUSDT" "STRAXUSDT" "TFUELUSDT" "YFIIUSDT" "ZRXUSDT" "DODOUSDT" "BZRXUSDT" "WTCUSDT" "VTHOUSDT" "CKBUSDT" "TWTUSDT" "SFPUSDT" "DIAUSDT" "UTKUSDT" "DEGOUSDT" "SKLUSDT" "PUNDIXUSDT" "MITHUSDT" "BELUSDT" "KNCUSDT" "OXTUSDT" "STORJUSDT" "AKROUSDT" "AUDIOUSDT" "AXSUSDT" "CVCUSDT" "TOMOUSDT" "IOTXUSDT" "BEAMUSDT" "MFTUSDT" "PONDUSDT" "BALUSDT" "UNFIUSDT" "IRISUSDT" "CELOUSDT" "CTKUSDT")

declare -a start_minutes_ago=30

declare -a future_flag=""

declare -a moonbot_flag=""

declare -a order_size_mb=0.0002
declare -a order_size_mt=400

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

echo Deleting old data files...
rm -rf ./../marketdata/shots/binance/spot/*
rm -rf ./../marketdata/tradedata/binance/spot/*
echo Done!

echo Processing shots for the last $start_minutes_ago minutes:
echo $start_date
echo $end_date

# Download tick trade data for all symbols
for symbol in "${symbol_list[@]}"
do
    python binance_trade_data.py -s $symbol -t $start_date -e $end_date $future_flag
done

# Detect shots information for all symbols
for symbol in "${symbol_list[@]}"
do
    python shots_detector.py -e binance -s $symbol $future_flag $moonbot_flag
done

# Calculate best PnL for all the shots
for symbol in "${symbol_list[@]}"
do
    python calc_shots_pnl.py -e binance -s $symbol $future_flag $moonbot_flag
done

# Generate strategy files for MB/MT
python strategy_generator.py -e binance -t $order_size_mb -y $order_size_mt $future_flag $moonbot_flag

mkdir $output_folder
cp ./../marketdata/shots/binance/spot/* $output_folder
cp ./../marketdata/shots/binance/spot/algorithms.config_spot $output_folder/../