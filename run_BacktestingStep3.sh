#! /bin/sh

strategyid=$1
runid=$2
testdaterange=20180901-20181130

declare exchange=bitfinex

pkill python
pkill python

python Backtesting_Step3.py -y $strategyid -r $runid -e $exchange -l Percentage -d $testdaterange
