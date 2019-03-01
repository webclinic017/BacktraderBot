#! /bin/sh


# declare -a arr_symbols=( "BTC/USDT" "ETH/USDT" "XRP/USDT" "LTC/USDT" "ETC/USDT" "IOTA/USDT" "EOS/USDT" "NEO/USDT" "ZEC/USDT" "ETP/USDT" "XMR/USDT"  "DASH/USDT")
declare -a arr_symbols=( "BTC/USDT" "LTC/USDT" "ETH/USDT" "XRP/USDT" "ETC/USDT" "IOTA/USDT" "EOS/USDT" "NEO/USDT" "ZEC/USDT" "ETP/USDT" "XMR/USDT"  "DASH/USDT")
#declare -a arr_timeframes=("1m" "5m" "15m" "30m" "1h" "3h" "6h" "12h" "1d")
declare -a arr_timeframes=("15m" "30m" "1h" "3h")

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
