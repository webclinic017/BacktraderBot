#! /bin/bash

declare -a runid="Run0072"
declare -a fname="Run0072_Step3.csv"

python backtest_analyzer.py -r $runid -f $fname
