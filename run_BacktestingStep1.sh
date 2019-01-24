#! /bin/sh

declare exchange="bitfinex"
declare -a arr_months=("1" "2" "3" "4" "5" "6" "7" "8" "9" "10" "11" "12")
declare -a arr_num_days=("31" "28" "31" "30" "31" "30" "31" "31" "30" "31" "30" "31")

#declare -a arr_symbols=("BTCUSDT"  "ETHUSDT" "XRPUSDT" "LTCUSDT" "ETCUSDT" "IOTAUSDT" "EOSUSDT" "NEOUSDT" "ZECUSDT" "ETPUSDT" "XMRUSDT" "DASHUSDT")
#declare -a arr_symbols=("BTCUSDT"  "ETHUSDT" "XRPUSDT" "LTCUSDT" "ETCUSDT" "IOTAUSDT" "EOSUSDT")
declare -a arr_symbols=("BTCUSDT")

#declare -a arr_timeframes=("15m" "30m" "1h" "3h" "6h" "12h")
declare -a arr_timeframes=("3h")
#declare -a arr_timeframes=("5m" "15m" "30m" "1h" "3h")

declare -a date_mode="Monthly" # Yearly/Monthly/Absolute
#declare -a backtest_years=("2017" "2018")

declare -a backtest_startdate="2018-03-01"
declare -a backtest_enddate="2018-03-31"

startyear=${backtest_startdate:0:4}
startmonth=${backtest_startdate:5:2}
startday=${backtest_startdate:8:2}
endyear=${backtest_enddate:0:4}
endmonth=${backtest_enddate:5:2}
endday=${backtest_enddate:8:2}
backtest_startmonth=$startyear-$startmonth
backtest_endmonth=$endyear-$endmonth

strategyid=$1
runid=$2

process_backtest() {
    _strategyid=${1}
    _runid=${2}
    _symbol=${3}
    _timeframe=${4}
    _fromyear=${5}
    _toyear=${6}
    _frommonth=$(printf "%02d" ${7})
    _tomonth=$(printf "%02d" ${8})
    _fromday=$(printf "%02d" ${9})
    _today=$(printf "%02d" ${10})
    daterange=$_fromyear$_frommonth$_fromday-$_toyear$_tomonth$_$today
    #echo INSIDE process_backtest: $_strategyid $_runid $_symbol $_timeframe $_fromyear $_toyear $_frommonth $_tomonth $_fromday $_today $daterange

    echo "\n\n\n---------------------------------------------------------------------------------------------------"
    echo "Running backtesting Step 1 of $_strategyid for $exchange/$symbol/$timeframe/$daterange"
    current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"

    #echo "--- Lot Size: 1 unit ---"
    #echo "\n********** Started: $current_date_time"
    #python Backtesting_Step1.py -y $_strategyid -s $symbol -e $exchange -t $timeframe -r $_runid -l Fixed -z 1 --fromyear $_fromyear --toyear $_toyear --frommonth $_frommonth --tomonth $_tomonth --fromday $_fromday --today $_today
    #current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
    #echo "********** Finished: $current_date_time"

    echo "--- Lot Size: 98% ---"
    echo "********** Started: $current_date_time"
    python Backtesting_Step1.py -y $_strategyid -s $symbol -e $exchange -t $timeframe -r $_runid -l Percentage -z 98 --fromyear $_fromyear --toyear $_toyear --frommonth $_frommonth --tomonth $_tomonth --fromday $_fromday --today $_today
    current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
    echo "********** Finished: $current_date_time"
}

for symbol in "${arr_symbols[@]}"
do
    for timeframe in "${arr_timeframes[@]}"
    do 
        for (( year=$startyear; year<=$endyear; year++))
        do 
            if [ $date_mode = "Yearly" ]
            then
                fromyear=$year
                toyear=$year
                frommonth=1
                tomonth=12
                fromday=1
                today=31
                #echo $strategyid $runid $symbol $timeframe $fromyear $toyear $frommonth $tomonth $fromday $today
                process_backtest $strategyid $runid $symbol $timeframe $fromyear $toyear $frommonth $tomonth $fromday $today
            fi        

            if [ $date_mode = "Monthly" ]
            then
                for month in {1..12}
                do
                    currmonth=$year-$(printf "%02d" $month)
                    if ([ "$currmonth" \> "$backtest_startmonth" ] || [ "$currmonth" = "$backtest_startmonth" ]) && ([ "$currmonth" \< "$backtest_endmonth" ] || [ "$currmonth" = "$backtest_endmonth" ])
                    then
                        fromyear=$year
                        toyear=$year
                        frommonth=$month
                        tomonth=$month
                        fromday=1
                        today=${arr_num_days[$month-1]}
                        #echo $strategyid $runid $symbol $timeframe $fromyear $toyear $frommonth $tomonth $fromday $today
                        process_backtest $strategyid $runid $symbol $timeframe $fromyear $toyear $frommonth $tomonth $fromday $today
                    fi
                done    
            fi     

            if [ $date_mode = "Absolute" ]
            then
                fromyear=$startyear
                toyear=$endyear
                frommonth=$startmonth
                tomonth=$endmonth
                fromday=$startday
                today=$endday
                #echo $strategyid $runid $symbol $timeframe $fromyear $toyear $frommonth $tomonth $fromday $today
                process_backtest $strategyid $runid $symbol $timeframe $fromyear $toyear $frommonth $tomonth $fromday $today
            fi         
        done    
    done
done

