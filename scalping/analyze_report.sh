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

declare -a db_filename=mtdb022.fdb
declare -a working_folder=/Users/alex/Downloads
declare -a remote_db_filename=c:/MoonTrader/data/mt-core/${db_filename}
declare -a local_db_filename=${working_folder}/${db_filename}

if [ -d "/Users/alex/opt/anaconda3" ]; then
    source /Users/alex/opt/anaconda3/etc/profile.d/conda.sh
elif [ -d "/home/alex/anaconda3" ]; then
    source /home/alex/anaconda3/etc/profile.d/conda.sh
elif [ -d "/Users/alex/anaconda3" ]; then
    source /Users/alex/anaconda3/etc/profile.d/conda.sh
fi
conda activate Backtrader

##pwsh ./powershell/get_from_vps.ps1 ${vps_ip_address} ${remote_db_filename} ${local_db_filename}

cd ..

python -m scalping.mt_report_analyzer