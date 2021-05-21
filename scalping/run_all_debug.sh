#! /bin/bash

declare -a symbol_list=("ONEUSDT" "UNFIUSDT")

declare -a start_minutes_ago=180

declare -a future_flag="-f"

declare -a moonbot_flag=""

declare -a order_size_mb=0.0002
declare -a order_size_mt=500

now_timestamp="$(date +'%s')"
now_timestamp=$((now_timestamp - now_timestamp % 60))

start_timestamp=$((now_timestamp - 60 * start_minutes_ago))
start_date="$(date -j -f "%s" "${start_timestamp}" "+%Y-%m-%dT%H:%M:%S")"
end_timestamp=$((start_timestamp + 60 * start_minutes_ago))
end_date="$(date -j -f "%s" "${end_timestamp}" "+%Y-%m-%dT%H:%M:%S")"

output_folder_prefix="$(date -j -f "%s" "${end_timestamp}" "+%Y%m%d_%H%M")"
output_folder="/Users/alex/Cloud@Mail.Ru/_TEMP/scalping/out/strategies/${output_folder_prefix}_Future_${start_minutes_ago}m/"

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

echo Processing shots for the past $start_minutes_ago minutes:
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
