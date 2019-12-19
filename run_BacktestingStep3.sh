#! /bin/bash

runid=$1
testdaterange=20170701-20170930
columnnameprefix=FwTest

declare exchange=bitfinex

pkill python
pkill python

python Backtesting_Step3.py -r $runid -d $testdaterange -p $columnnameprefix
