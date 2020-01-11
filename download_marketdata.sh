#! /bin/bash


#declare -a arr_symbols=( "BTC/USD" "ETH/USD" "LTC/USD" "XRP/USD" "ETC/USD" "IOTA/USD" "EOS/USD" "NEO/USD" "ZEC/USD" "ETP/USD" "XMR/USD"  "DASH/USD")
#declare -a arr_symbols=( "BTC/USD" "ETH/USD" "LTC/USD" "XRP/USD" "ETC/USD" "IOTA/USD" "EOS/USD" "NEO/USD" "ZEC/USD" )
declare -a arr_symbols=( "BTC/USD")

#declare -a arr_timeframes=("1m" "5m" "15m" "30m" "1h" "3h" "6h" "12h" "1d")
declare -a arr_timeframes=("1h" "1d")


declare exchange="bitfinex"

for symbol in "${arr_symbols[@]}"
do

    for timeframe in "${arr_timeframes[@]}"
    do
        echo "Downloading market data for $exchange/$symbol/$timeframe..."
        current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
        echo "Started: $current_date_time... "
        python ccxt_market_data.py -s $symbol -e $exchange -t $timeframe
        current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
        echo "Finished: $current_date_time."
    done
done
