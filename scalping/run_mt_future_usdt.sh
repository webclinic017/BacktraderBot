#! /bin/bash

#declare -a symbol_list=("BTCUSDT" "1000SHIBUSDT" "1INCHUSDT" "AAVEUSDT" "AKROUSDT" "ALGOUSDT" "ALICEUSDT" "ALPHAUSDT" "ANKRUSDT" "ATAUSDT" "ATOMUSDT" "AUDIOUSDT" "AVAXUSDT" "AXSUSDT" "BAKEUSDT" "BALUSDT" "BANDUSDT" "BATUSDT" "BCHUSDT" "BELUSDT" "BLZUSDT" "BTSUSDT" "BTTUSDT" "BZRXUSDT" "C98USDT" "CELRUSDT" "CHRUSDT" "CHZUSDT" "COMPUSDT" "COTIUSDT" "CRVUSDT" "CTKUSDT" "CVCUSDT" "DEFIUSDT" "DENTUSDT" "DGBUSDT" "DODOUSDT" "DOGEUSDT" "DOTUSDT" "EGLDUSDT" "ENJUSDT" "EOSUSDT" "ETCUSDT" "FILUSDT" "FLMUSDT" "FTMUSDT" "GRTUSDT" "GTCUSDT" "HBARUSDT" "HNTUSDT" "HOTUSDT" "ICPUSDT" "ICXUSDT" "IOSTUSDT" "IOTAUSDT" "IOTXUSDT" "KAVAUSDT" "KEEPUSDT" "KNCUSDT" "KSMUSDT" "LINAUSDT" "LINKUSDT" "LITUSDT" "LRCUSDT" "LUNAUSDT" "MANAUSDT" "MASKUSDT" "MATICUSDT" "MKRUSDT" "MTLUSDT" "NEARUSDT" "NEOUSDT" "NKNUSDT" "OCEANUSDT" "OGNUSDT" "OMGUSDT" "ONEUSDT" "ONTUSDT" "QTUMUSDT" "RAYUSDT" "REEFUSDT" "RENUSDT" "RLCUSDT" "RSRUSDT" "RUNEUSDT" "RVNUSDT" "SANDUSDT" "SCUSDT" "SFPUSDT" "SKLUSDT" "SNXUSDT" "SOLUSDT" "SRMUSDT" "STMXUSDT" "STORJUSDT" "SUSHIUSDT" "SXPUSDT" "THETAUSDT" "TLMUSDT" "TOMOUSDT" "TRBUSDT" "TRXUSDT" "UNFIUSDT" "UNIUSDT" "VETUSDT" "WAVESUSDT" "XEMUSDT" "XLMUSDT" "XMRUSDT" "XTZUSDT" "YFIIUSDT" "YFIUSDT" "ZECUSDT" "ZENUSDT" "ZILUSDT" "ZRXUSDT")
#declare -a symbol_list=("AAVEUSDT" "AKROUSDT" "ALICEUSDT" "ALPHAUSDT" "AVAXUSDT" "AXSUSDT" "BALUSDT" "BANDUSDT" "BELUSDT" "BLZUSDT" "BZRXUSDT" "CHRUSDT" "COTIUSDT" "DODOUSDT" "DOGEUSDT" "ENJUSDT" "FLMUSDT" "FTMUSDT" "GRTUSDT" "HBARUSDT" "HNTUSDT" "ICXUSDT" "IOSTUSDT" "LITUSDT" "LUNAUSDT" "MANAUSDT" "NEARUSDT" "ONEUSDT" "REEFUSDT" "RLCUSDT" "RUNEUSDT" "RVNUSDT" "SANDUSDT" "SFPUSDT" "SKLUSDT" "SNXUSDT" "STMXUSDT" "STORJUSDT" "THETAUSDT" "TOMOUSDT" "TRBUSDT" "UNFIUSDT" "ZRXUSDT")

declare -a excluded_symbols_regex="BTCUSDT BTCSTUSDT BNBUSDT ETHUSDT LTCUSDT XRPUSDT"

python get_symb ols.py -q USDT -f

declare -a symbol_list
while read line; do
    symbol_list+=($line)
done < symbols_future_usdt.txt

declare -a start_minutes_ago=$((8*60))

declare -a ultrashortmode=${1}

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

if [ -d "/Users/alex/opt/anaconda3" ]; then
    source /Users/alex/opt/anaconda3/etc/profile.d/conda.sh
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

echo Detecting shots for the last $start_minutes_ago minutes:
echo $start_date
echo $end_date

for symbol in "${symbol_list[@]}"
do
    if printf "${excluded_symbols_regex}" | grep -q ${symbol}; then
        echo Skipping excluded symbol: ${symbol} ...
            continue
    fi
    # Download tick trade data for all symbols
    python binance_trade_data.py -s $symbol -t $start_date -e $end_date $future_flag

    # Detect shots information for all symbols
    python shots_detector.py ${ultrashortmode} -e binance -s $symbol $future_flag $moonbot_flag

    # Calculate best PnL for all the shots
    python calc_shots_pnl.py ${ultrashortmode} -e binance -s $symbol $future_flag $moonbot_flag
done


# Generate strategy files for MB/MT
cd ..
python -m scalping.strategy_generator -e binance $future_flag $moonbot_flag
cd scalping

mkdir $output_folder
cp ./../marketdata/shots/binance/future/* $output_folder
cp ./../marketdata/shots/binance/future/algorithms.config_future $output_folder/../