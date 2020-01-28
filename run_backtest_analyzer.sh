#! /bin/bash

declare -a runid="Run0073"
declare -a fname="Run0073_Step1.csv"

python backtest_analyzer.py -r $runid -f $fname
