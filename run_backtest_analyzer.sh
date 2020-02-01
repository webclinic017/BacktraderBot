#! /bin/bash

declare -a runid="Run0071"
declare -a fname="Run0071_Step1.csv"

python backtest_analyzer.py -r $runid -f $fname
