#! /bin/sh


#declare -a arr_symbols=("BTCUSDT"  "ETHUSDT" "XRPUSDT" "LTCUSDT" "ETCUSDT" "IOTAUSDT" "EOSUSDT" "NEOUSDT" "ZECUSDT" "ETPUSDT" "XMRUSDT" "DASHUSDT")
declare -a arr_symbols=("BTCUSDT"  "ETHUSDT" "LTCUSDT")

#declare -a arr_timeframes=("30m" "1h" "3h" "6h" "12h")
declare -a arr_timeframes=("12h")

declare exchange="bitfinex"

for symbol in "${arr_symbols[@]}"
do
    for timeframe in "${arr_timeframes[@]}"
    do
        echo "Running Alex (Noro) TrendMAs v2.3 Strategy for $exchange/$symbol/$timeframe..."
        current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
        echo "Lot Size: 1 unit"
        echo "Started: $current_date_time..."
        python BatchAlex_Noro_TrendMAsStrategy_v2_3.py -s $symbol -e $exchange -t $timeframe -b 90 -p $1 -l Fixed -z 1 
        current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
        echo "Finished: $current_date_time"

        echo "Lot Size: 98%"
        echo "Started: $current_date_time..."
        python BatchAlex_Noro_TrendMAsStrategy_v2_3.py -s $symbol -e $exchange -t $timeframe -b 90 -p $1 -l Percentage -z 98
        current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
        echo "Finished: $current_date_time"

    done
done
