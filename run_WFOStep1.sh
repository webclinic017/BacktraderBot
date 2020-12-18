#! /bin/bash

declare exchange="bitfinex"
declare -a arr_months=("1" "2" "3" "4" "5" "6" "7" "8" "9" "10" "11" "12")
declare -a arr_num_days=("31" "28" "31" "30" "31" "30" "31" "31" "30" "31" "30" "31")

runid=$1

declare -a wfo_startdate="2018-03-01"

startyear=${wfo_startdate:0:4}
startmonth=${wfo_startdate:5:2}
startday=${wfo_startdate:8:2}

wfo_training_period=365
wfo_testing_period=60
num_wfo_cycles=3

#declare -a arr_strategies=("S001_AlexNoroTrendMAsStrategy" "S002_AlexNoroSILAStrategy" "S003_AlexNoroRobotBitMEXFastRSIStrategy" "S004_AlexNoroBandsScalperStrategy" "S005_AlexNoroTripleRSIStrategy" "S006_AlexNoroSqueezeMomentumStrategy" "S007_AlexNoroMultimaStrategy" "S008_AlexNoroSuperTrendStrategy" "S009_RSIMinMaxStrategy" "S010_AlexAroonTrendStrategy" "S011_EMACrossOverStrategy")
declare -a arr_strategies=("S001_AlexNoroTrendMAsStrategy" "S002_AlexNoroSILAStrategy" "S003_AlexNoroRobotBitMEXFastRSIStrategy" "S004_AlexNoroBandsScalperStrategy" "S005_AlexNoroTripleRSIStrategy" "S006_AlexNoroSqueezeMomentumStrategy" "S007_AlexNoroMultimaStrategy" "S008_AlexNoroSuperTrendStrategy" "S010_AlexAroonTrendStrategy" "S011_EMACrossOverStrategy")

#declare -a arr_symbols=("BTCUSD" "ETHUSD" "XRPUSD" "LTCUSD" "ETCUSD" "IOTAUSD" "EOSUSD" "NEOUSD" "ZECUSD" "ETPUSD" "XMRUSD" "DASHUSD")
declare -a arr_symbols=("BTCUSD")

#declare -a arr_timeframes=("15m" "30m" "1h" "3h" "6h" "12h")
declare -a arr_timeframes=("30m" "1h")

if [ -d "/opt/anaconda3" ]; then
    source /opt/anaconda3/etc/profile.d/conda.sh
elif [ -d "/home/alex/anaconda3" ]; then
    source /home/alex/anaconda3/etc/profile.d/conda.sh
elif [ -d "/Users/alex/anaconda3" ]; then
    source /Users/alex/anaconda3/etc/profile.d/conda.sh
fi
conda activate Backtrader

run_WFO_training() {
    _runid=${1}
    _strategyid=${2}
    _symbol=${3}
    _timeframe=${4}

    echo "---------------------------------------------------------------------------------------------------"
    echo "Running WFO Step 1: Training Cycles for $_strategyid/$exchange/$_symbol/$_timeframe"
    current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"

    echo "********** Started: $current_date_time"
    python WFO_Step1.py -r $_runid --startyear $startyear --startmonth $startmonth --startday $startday --num_wfo_cycles $num_wfo_cycles --wfo_training_period $wfo_training_period --wfo_testing_period $wfo_testing_period -y $_strategyid -e $exchange -s $_symbol -t $_timeframe
    current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
    echo "********** Finished: $current_date_time"
}

for strategyid in "${arr_strategies[@]}"
do
    for symbol in "${arr_symbols[@]}"
    do
        for timeframe in "${arr_timeframes[@]}"
        do
            pkill python

            run_WFO_training $runid $strategyid $symbol $timeframe
        done
    done
done

