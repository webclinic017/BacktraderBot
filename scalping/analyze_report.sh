#! /bin/bash

if [[ $# -eq 0 || $# -ge 3 ]]; then
    echo "Please specify valid parameters to run the script: analyze_report.sh <VPS_ID:1|2> <append deltas:y|n>"
    exit -1
fi

declare -a vps_id_param=${1}
declare -a append_deltas=${2}

if [[ "$vps_id_param" == "1" ]]; then
    declare -a vps_ip_address=45.76.214.140
elif [[ "$vps_id_param" == "2" ]]; then
    declare -a vps_ip_address=167.179.72.2
else
    echo "Invalid VPS ID specified: ${vps_id_param}"
    exit -1
fi

declare -a working_folder=/Users/alex/Downloads

if [ -d "/Users/alex/opt/anaconda3" ]; then
    source /Users/alex/opt/anaconda3/etc/profile.d/conda.sh
elif [ -d "/home/alex/anaconda3" ]; then
    source /home/alex/anaconda3/etc/profile.d/conda.sh
elif [ -d "/Users/alex/anaconda3" ]; then
    source /Users/alex/anaconda3/etc/profile.d/conda.sh
fi
conda activate Backtrader

echo Deploying MT Report Analyzer on VPS$vps_id_param
scp ./mt_report_analyzer.py $vps_ip_address:c:/Python/Scalping/mt_report_analyzer.py

echo Running MT Report Analyzer
ssh $vps_ip_address "python c:/Python/Scalping/mt_report_analyzer.py"

echo Copying remote report files into $working_folder
scp $vps_ip_address:c:/Python/Scalping/\*.xlsx $working_folder

echo Cleaning up on VPS$vps_id_param
ssh $vps_ip_address "del c:\Python\Scalping\*.xlsx"

if [[ "$append_deltas" == "y" ]]; then
    cd ..
    python -m scalping.mt_report_deltas_appender
fi
