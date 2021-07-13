#! /bin/bash

if [[ $# -ne 2 ]]; then
    echo "Please specify valid parameters to run the script: analyze_report.sh <DEFAULT_TP_PCT> <DEFAULT_SL_PCT>"
    exit -1
fi

declare -a default_tp_pct_value=$1
declare -a default_sl_pct_value=$2

if [ -d "/opt/anaconda3" ]; then
    source /opt/anaconda3/etc/profile.d/conda.sh
elif [ -d "/home/alex/anaconda3" ]; then
    source /home/alex/anaconda3/etc/profile.d/conda.sh
elif [ -d "/Users/alex/anaconda3" ]; then
    source /Users/alex/anaconda3/etc/profile.d/conda.sh
fi
conda activate Backtrader

cd ..

python -m scalping.tmm_report_analyzer -t ${default_tp_pct_value} -s ${default_sl_pct_value}