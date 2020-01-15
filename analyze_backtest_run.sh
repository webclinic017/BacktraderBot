#! /bin/bash

declare -a runid="Run0033"
declare -a fname="Run0033_Step3.csv"

python backtest_analyzer.py -r $runid -f $fname
