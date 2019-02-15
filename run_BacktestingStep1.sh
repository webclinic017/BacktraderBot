#! /bin/sh

declare exchange="bitfinex"
declare -a arr_months=("1" "2" "3" "4" "5" "6" "7" "8" "9" "10" "11" "12")
declare -a arr_num_days=("31" "28" "31" "30" "31" "30" "31" "31" "30" "31" "30" "31")

#declare -a arr_strategies=("S001_AlexNoroTrendMAsStrategy" "S002_AlexNoroSILAStrategy" "S003_AlexNoroRobotBitMEXFastRSIStrategy" "S004_AlexNoroBandsScalperStrategy" "S005_AlexNoroTripleRSIStrategy" "S006_AlexNoroSqueezeMomentumStrategy" "S007_AlexNoroMultimaStrategy" "S008_AlexNoroSuperTrendStrategy")
#declare -a arr_strategies=("S001_AlexNoroTrendMAsStrategy" "S002_AlexNoroSILAStrategy" "S003_AlexNoroRobotBitMEXFastRSIStrategy" "S004_AlexNoroBandsScalperStrategy" "S005_AlexNoroTripleRSIStrategy" "S006_AlexNoroSqueezeMomentumStrategy" "S007_AlexNoroMultimaStrategy" "S008_AlexNoroSuperTrendStrategy")
declare -a arr_strategies=("S008_AlexNoroSuperTrendStrategy")

#declare -a arr_symbols=("BTCUSDT"  "ETHUSDT" "XRPUSDT" "LTCUSDT" "ETCUSDT" "IOTAUSDT" "EOSUSDT" "NEOUSDT" "ZECUSDT" "ETPUSDT" "XMRUSDT" "DASHUSDT")
declare -a arr_symbols=("BTCUSDT" "LTCUSDT")
#declare -a arr_symbols=("BTCUSDT"  "ETHUSDT")

#declare -a arr_timeframes=("15m" "30m" "1h" "3h" "6h" "12h")
declare -a arr_timeframes=("3h")

declare -a backtest_startdate="2014-01-01"
declare -a backtest_enddate="2017-06-30"

startyear=${backtest_startdate:0:4}
startmonth=${backtest_startdate:5:2}
startday=${backtest_startdate:8:2}
endyear=${backtest_enddate:0:4}
endmonth=${backtest_enddate:5:2}
endday=${backtest_enddate:8:2}

runid=$1

process_backtest() {
    _strategyid=${1}
    _runid=${2}
    _symbol=${3}
    _timeframe=${4}
    _fromyear=${5}
    _toyear=${6}
    _frommonth=${7}
    _tomonth=${8}
    _fromday=${9}
    _today=${10}
    daterange=$_fromyear$_frommonth$_fromday-$_toyear$_tomonth$_$today
    monthlystatsprefix="BkTest"
    #echo INSIDE process_backtest: $_strategyid $_runid $_symbol $_timeframe $_fromyear $_toyear $_frommonth $_tomonth $_fromday $_today $daterange

    echo "\n\n\n---------------------------------------------------------------------------------------------------"
    echo "Running backtesting Step 1 for $_strategyid/$exchange/$symbol/$timeframe/$daterange"
    current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"

    echo "********** Started: $current_date_time"
    python Backtesting_Step1.py -y $_strategyid -r $_runid -e $exchange -s $symbol -t $timeframe -l Fixed --fromyear $_fromyear --toyear $_toyear --frommonth $_frommonth --tomonth $_tomonth --fromday $_fromday --today $_today --monthlystatsprefix $monthlystatsprefix
    current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
    echo "********** Finished: $current_date_time"
}

pkill python
pkill python

for strategyid in "${arr_strategies[@]}"
do
    for symbol in "${arr_symbols[@]}"
    do
        for timeframe in "${arr_timeframes[@]}"
        do
            pkill python
            pkill python

            fromyear=$startyear
            toyear=$endyear
            frommonth=$startmonth
            tomonth=$endmonth
            fromday=$startday
            today=$endday
            #echo !!! $strategyid $runid $symbol $timeframe $fromyear $toyear $frommonth $tomonth $fromday $today
            process_backtest $strategyid $runid $symbol $timeframe $fromyear $toyear $frommonth $tomonth $fromday $today
        done
    done
done

