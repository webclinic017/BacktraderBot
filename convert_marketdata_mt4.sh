#! /bin/sh


declare -a arr_symbols=( "BTCUSDT" )
declare -a arr_timeframes=( "1m" )

declare exchange="bitfinex"

for symbol in "${arr_symbols[@]}"
do

    for timeframe in "${arr_timeframes[@]}"
    do
        echo "Converting market data to MT4 format for: $exchange/$symbol/$timeframe..."
        current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
        echo "Started: $current_date_time... "
        python convert_marketdata_mt4.py -s $symbol -e $exchange -t $timeframe
        current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
        echo "Finished: $current_date_time."
    done
done
