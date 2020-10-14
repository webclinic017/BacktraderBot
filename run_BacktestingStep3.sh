#! /bin/bash

runid=$1
testdaterange=20180701-20180831
columnnameprefix=FwTest

declare exchange=bitfinex

pkill python
pkill python

if [ -d "/opt/anaconda3" ]; then
    source /opt/anaconda3/etc/profile.d/conda.sh
elif [ -d "/home/alex/anaconda3" ]; then
    source /home/alex/anaconda3/etc/profile.d/conda.sh
elif [ -d "/Users/alex/anaconda3" ]; then
    source /Users/alex/anaconda3/etc/profile.d/conda.sh
fi
conda activate Backtrader

python Backtesting_Step3.py -r $runid -d $testdaterange -p $columnnameprefix
