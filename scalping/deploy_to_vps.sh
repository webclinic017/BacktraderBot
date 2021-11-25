#! /bin/bash

if [[ $# -ne 2 ]]; then
    echo "Please specify valid parameters to run the script: deploy_to_vps.sh <STRATEGY_FILE_TYPE:f|s|fs|fwl> <VPS_ID:1|2>"
    exit -1
fi

declare -a file_type_param=${1}
declare -a vps_id_param=${2}

if [[ "$file_type_param" == "f" ]]; then
    declare -a filename=algorithms.config_future
elif [[ "$file_type_param" == "s" ]]; then
    declare -a filename=algorithms.config_spot
elif [[ "$file_type_param" == "fs" ]]; then
    declare -a filename=algorithms.config_future_spot
elif [[ "$file_type_param" == "fwl" ]]; then
    declare -a filename=algorithms.config_future_wl
else
    echo "Invalid file type specified: ${file_type_param}"
    exit -1
fi


if [[ "$vps_id_param" == "1" ]]; then
    declare -a vps_ip_address=45.76.214.140
elif [[ "$vps_id_param" == "2" ]]; then
    declare -a vps_ip_address=167.179.72.2
else
    echo "Invalid VPS ID specified: ${vps_id_param}"
    exit -1
fi

declare -a filepath=/Users/alex/Cloud@Mail.Ru/_TEMP/scalping/out/strategies/${filename}

if [[ ! -f ${filepath} ]]; then
    echo "File ${filepath} not found!"
fi

pwsh ./powershell/deploy_to_vps.ps1 ${filepath} ${vps_ip_address}