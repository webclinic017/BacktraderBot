#! /bin/sh

declare exchange="bitfinex"

#declare -a arr_symbols=("BTCUSDT"  "ETHUSDT" "XRPUSDT" "LTCUSDT" "ETCUSDT" "IOTAUSDT" "EOSUSDT" "NEOUSDT" "ZECUSDT" "ETPUSDT" "XMRUSDT" "DASHUSDT")
declare -a arr_symbols=("BTCUSDT"  "ETHUSDT" "XRPUSDT" "LTCUSDT" "ETCUSDT" "IOTAUSDT" "EOSUSDT")

#declare -a arr_timeframes=("30m" "1h" "3h" "6h" "12h")
declare -a arr_timeframes=("15m" "30m" "1h" "3h")

declare -a date_mode="Monthly" # Yearly/Monthly
#declare -a arr_years=("2017" "2018")
declare -a arr_years=("2018")
#declare -a arr_months=("1" "2" "3" "4" "5" "6" "7" "8" "9" "10" "11" "12")
declare -a arr_months=("1" "2" "3" "4" "5" "6" "7" "8")
declare -a arr_num_days=("31" "28" "31" "30" "31" "30" "31" "31" "30" "31" "30" "31")

process_backtest() {
    _prefix=$1
    _symbol=$2 
    _timeframe=$3 
    _year=$4 
    _frommonth=$(printf "%02d" $5)
    _tomonth=$(printf "%02d" $6)  
    _fromday=$(printf "%02d" $7) 
    _today=$(printf "%02d" $8)
    daterange=$_year$_frommonth$_fromday-$_year$_tomonth$_$today
    #echo INSIDE: $_prefix $_symbol $_timeframe $_year $_frommonth $_tomonth $_fromday $_today $daterange

    echo "---------------------------------------------------------------------------------------------------"
    echo "Running Alex (Noro) TrendMAs v2.3 Strategy for $exchange/$symbol/$timeframe/$daterange"
    current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"

    #echo "\n********** Started: $current_date_time"
    #echo "--- Lot Size: 1 unit ---"
    #python BatchAlex_Noro_TrendMAsStrategy_v2_3.py -s $symbol -e $exchange -t $timeframe -p $_prefix -l Fixed -z 1 --fromyear $_year --toyear $_year --frommonth $_frommonth --tomonth $_tomonth --fromday $_fromday --today $_today
    #current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
    #echo "********** Finished: $current_date_time"

    echo "\n********** Started: $current_date_time"
    echo "--- Lot Size: 98% ---"
    python BatchAlex_Noro_TrendMAsStrategy_v2_3.py -s $symbol -e $exchange -t $timeframe -p $_prefix -l Percentage -z 98 --fromyear $_year --toyear $_year --frommonth $_frommonth --tomonth $_tomonth --fromday $_fromday --today $_today
    current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
    echo "********** Finished: $current_date_time"
}

for symbol in "${arr_symbols[@]}"
do
    for timeframe in "${arr_timeframes[@]}"
    do
        for year in "${arr_years[@]}"
        do
            if [ $date_mode = "Yearly" ]
            then
                frommonth=1
                tomonth=12
                fromday=1
                today=31
                process_backtest $1 $symbol $timeframe $year $frommonth $tomonth $fromday $today
            fi        

            if [ $date_mode = "Monthly" ]
            then
                for month in "${arr_months[@]}"
                do
                    frommonth=$month
                    tomonth=$month
                    fromday=1
                    today=${arr_num_days[$month-1]}
                    process_backtest $1 $symbol $timeframe $year $frommonth $tomonth $fromday $today
                done    
            fi            
        done    
    done
done

