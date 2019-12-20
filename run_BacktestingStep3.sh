#! /bin/bash

runid=$1
testdaterange=20140401-20140531
columnnameprefix=FwTest

declare exchange=bitfinex

pkill python
pkill python

python Backtesting_Step3.py -r $runid -d $testdaterange -p $columnnameprefix
