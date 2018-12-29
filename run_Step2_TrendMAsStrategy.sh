#! /bin/sh

runid=$1

declare exchange="bitfinex"

python Step2_Alex_Noro_TrendMAsStrategy_v2_3.py -e $exchange -r $runid