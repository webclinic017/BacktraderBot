#! /bin/bash

declare -a symbol_list=("ALPHAUSDT" "AVAXUSDT" "AXSUSDT" "BZRXUSDT" "CHRUSDT" "CHZUSDT" "CRVUSDT" "CTKUSDT" "DODOUSDT" "DOTUSDT" "EGLDUSDT" "ENJUSDT" "FLMUSDT" "FTMUSDT" "GRTUSDT" "KAVAUSDT" "KSMUSDT" "LITUSDT" "LUNAUSDT" "MANAUSDT" "MKRUSDT" "NEOUSDT" "ONEUSDT" "ONTUSDT" "SANDUSDT" "SKLUSDT" "SOLUSDT" "SUSHIUSDT" "SXPUSDT" "THETAUSDT" "TRBUSDT" "VETUSDT" "XTZUSDT" "ZECUSDT" "ZRXUSDT")

declare -a start_hours_ago=200

declare -a future_flag="-f"

declare -a moonbot_flag=""

declare -a order_size_mb=0.0002
declare -a order_size_mt=400

now_timestamp="$(date +'%s')"
now_timestamp=$((now_timestamp - now_timestamp % 60))

start_timestamp=$((now_timestamp - 3600 * start_hours_ago))
start_date="$(date -j -f "%s" "${start_timestamp}" "+%Y-%m-%dT%H:%M:%S")"
end_timestamp=$((start_timestamp + 3600 * start_hours_ago))
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
rm -rf ./../marketdata/shots/binance/future/*
rm -rf ./../marketdata/tradedata/binance/future/*
echo Done!

echo Processing shots for the last $start_hours_ago hours:
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


