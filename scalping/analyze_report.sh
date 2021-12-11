#! /bin/bash

if [[ $# -ne 1 ]]; then
    echo "Please specify valid parameters to run the script: analyze_report.sh <VPS_ID:1|2>"
    exit -1
fi

declare -a vps_id_param=${1}

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

echo Running MT Report Analyzer on VPS$vps_id_param
ssh $vps_ip_address "python c:/Python/Scalping/mt_report_analyzer.py"

echo Copying remote report files into $working_folder

scp 45.76.214.140:c:/Python/Scalping/\*csv $working_folder

echo Deleting old analyzer files on VPS$vps_id_param
ssh $vps_ip_address "del c:\Python\Scalping\*.csv"