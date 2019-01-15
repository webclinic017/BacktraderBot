#! /bin/sh

strategyid=$1
runid=$2

declare exchange="bitfinex"

python Backtesting_Step2.py -y $strategyid -r $runid -e $exchange