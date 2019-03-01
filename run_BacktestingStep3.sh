#! /bin/sh

runid=$1
testdaterange=20170701-20190228
columnnameprefix=FwTest

declare exchange=bitfinex

pkill python
pkill python

python Backtesting_Step3.py -r $runid -l Fixed -d $testdaterange -p $columnnameprefix
