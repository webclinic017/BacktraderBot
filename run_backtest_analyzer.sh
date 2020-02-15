#! /bin/bash

declare -a runid="TTT0074"
declare -a fname="TTT0074_Step1.csv"

if [ -d "/opt/anaconda3" ]; then
    source /opt/anaconda3/etc/profile.d/conda.sh
elif [ -d "/home/alex/anaconda3" ]; then
    source /home/alex/anaconda3/etc/profile.d/conda.sh
elif [ -d "/Users/alex/anaconda3" ]; then
    source /Users/alex/anaconda3/etc/profile.d/conda.sh
fi
conda activate Backtrader

python backtest_analyzer.py -r $runid -f $fname
