#! /bin/bash

if [[ $# -ne 1 ]]; then
    echo "Please specify valid parameters to run the script: analyze_report.sh <DEFAULT_SL_PCT>"
    exit -1
fi

declare -a default_sl_pct_value=$1

if [ -d "/opt/anaconda3" ]; then
    source /opt/anaconda3/etc/profile.d/conda.sh
elif [ -d "/home/alex/anaconda3" ]; then
    source /home/alex/anaconda3/etc/profile.d/conda.sh
elif [ -d "/Users/alex/anaconda3" ]; then
    source /Users/alex/anaconda3/etc/profile.d/conda.sh
fi
conda activate Backtrader

cd ..

python -m scalping.tmm_report_analyzer -s ${default_sl_pct_value}