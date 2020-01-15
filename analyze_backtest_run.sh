#! /bin/bash

declare -a runid="Run0070"
declare -a fname="Run0070_Step1.csv"

python backtest_analyzer.py -r $runid -f $fname
