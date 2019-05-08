#! /bin/sh

runid=$1
testdaterange=20180801-20190228
columnnameprefix=FwTest

declare exchange=bitfinex

pkill python
pkill python

python ./steps/Backtesting_Step3.py -r $runid -d $testdaterange -p $columnnameprefix
