#! /bin/bash

declare -a symbol_list=("1000SHIBUSDT" "1INCHUSDT" "AAVEUSDT" "ADAUSDT" "AKROUSDT" "ALGOUSDT" "ALICEUSDT" "ALPHAUSDT" "ANKRUSDT" "ATOMUSDT" "AVAXUSDT" "AXSUSDT" "BALUSDT" "BANDUSDT" "BATUSDT" "BCHUSDT" "BELUSDT" "BLZUSDT" "BTSUSDT" "BZRXUSDT" "CHRUSDT" "CHZUSDT" "COMPUSDT" "COTIUSDT" "CRVUSDT" "CTKUSDT" "CVCUSDT" "DASHUSDT" "DODOUSDT" "DOGEUSDT" "DOTUSDT" "EGLDUSDT" "ENJUSDT" "EOSUSDT" "ETCUSDT" "FILUSDT" "FLMUSDT" "FTMUSDT" "GRTUSDT" "HBARUSDT" "HNTUSDT" "ICXUSDT" "IOSTUSDT" "IOTAUSDT" "KAVAUSDT" "KNCUSDT" "KSMUSDT" "LINKUSDT" "LITUSDT" "LRCUSDT" "LUNAUSDT" "MANAUSDT" "MATICUSDT" "MKRUSDT" "NEARUSDT" "NEOUSDT" "OCEANUSDT" "OMGUSDT" "ONEUSDT" "ONTUSDT" "QTUMUSDT" "REEFUSDT" "RENUSDT" "RLCUSDT" "RSRUSDT" "RUNEUSDT" "RVNUSDT" "SANDUSDT" "SFPUSDT" "SKLUSDT" "SNXUSDT" "SOLUSDT" "SRMUSDT" "STMXUSDT" "STORJUSDT" "SUSHIUSDT" "SXPUSDT" "THETAUSDT" "TOMOUSDT" "TRBUSDT" "TRXUSDT" "UNFIUSDT" "UNIUSDT" "VETUSDT" "WAVESUSDT" "XEMUSDT" "XLMUSDT" "XMRUSDT" "XRPUSDT" "XTZUSDT" "YFIIUSDT" "YFIUSDT" "ZECUSDT" "ZENUSDT" "ZILUSDT" "ZRXUSDT")

declare -a start_minutes_ago=20

declare -a future_flag="-f"

declare -a moonbot_flag=""

now_timestamp="$(date +'%s')"
now_timestamp=$((now_timestamp - now_timestamp % 60))

start_timestamp=$((now_timestamp - 60 * start_minutes_ago))
start_date="$(date -j -f "%s" "${start_timestamp}" "+%Y-%m-%dT%H:%M:%S")"
end_timestamp=$((start_timestamp + 60 * start_minutes_ago))
end_date="$(date -j -f "%s" "${end_timestamp}" "+%Y-%m-%dT%0H:%M:%S")"

output_folder_prefix="$(date -j -f "%s" "${end_timestamp}" "+%Y%m%d_%H%M")"
BASE_OUT_FOLDER=/Users/alex/Cloud@Mail.Ru/_TEMP/scalping/out/strategies
output_folder="${BASE_OUT_FOLDER}/${output_folder_prefix}_Future_${start_minutes_ago}m/"

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

for symbol in "${symbol_list[@]}"
do
    # Download tick trade data for all symbols
    python binance_trade_data.py -s $symbol -t $start_date -e $end_date $future_flag

    # Detect shots information for all symbols
    python shots_detector.py -e binance -s $symbol $future_flag $moonbot_flag

    # Calculate best PnL for all the shots
    python calc_shots_pnl.py -e binance -s $symbol $future_flag $moonbot_flag
done

# Generate strategy files for MB/MT
python strategy_generator.py -e binance $future_flag $moonbot_flag

mkdir $output_folder
cp ./../marketdata/shots/binance/future/* $output_folder
cp ./../marketdata/shots/binance/future/algorithms.config_future $output_folder/../