#! /bin/bash

declare -a runid="Run0069"
declare -a fname="Run0069_Step1.csv"

python backtest_analyzer.py -r $runid -f $fname
