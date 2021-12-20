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

declare -a working_folder=/Users/alex/Cloud@Mail.Ru/_TEMP/scalping/out/strategies
declare -a filepath=${working_folder}/${filename}
declare -a remote_filename=c:/MoonTrader/data/mt-core/algorithms.config
declare -a remote_filename_backup=c:/MoonTrader/data/mt-core/algorithms.config_BACKUP
declare -a local_filename=${working_folder}/algorithms.config_REMOTE

if [[ ! -f ${filepath} ]]; then
    echo "File ${filepath} not found!"
fi

echo Retrieving MT strategy file from VPS${vps_id_param}
scp $vps_ip_address:${remote_filename} ${local_filename}

echo
echo Backing up the exising MT strategy on VPS${vps_id_param}
scp ${local_filename} $vps_ip_address:${remote_filename_backup}

echo
echo Deploying the new MT strategy file on VPS${vps_id_param}
scp ${filepath} $vps_ip_address:${remote_filename}

echo
echo Cleaning up.
rm -rf $local_filename
