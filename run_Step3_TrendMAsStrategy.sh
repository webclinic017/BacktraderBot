#! /bin/sh

runid=$1
testdaterange=20180901-20181130

declare exchange=bitfinex

python Step3_Alex_Noro_TrendMAsStrategy_v2_3.py -e $exchange -r $runid -l Percentage -d $testdaterange
