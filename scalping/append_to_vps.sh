#! /bin/bash

if [[ $# -ne 2 ]]; then
    echo "Please specify valid parameters to run the script: append_to_vps.sh <STRATEGY_FILE_TYPE:f|s|fs|fwl> <VPS_ID:1>"
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
else
    echo "Invalid VPS ID specified: ${vps_id_param}"
    exit -1
fi

declare -a working_folder=/Users/alex/Downloads
declare -a file_to_append=${working_folder}/${filename}
declare -a remote_filename=${working_folder}/algorithms.config_REMOTE
declare -a output_filename=${working_folder}/algorithms.config_MERGED

if [[ ! -f ${file_to_append} ]]; then
    echo "File ${file_to_append} not found!"
fi

pwsh ./powershell/get_from_vps.ps1 ${vps_ip_address} ${remote_filename}

sed '$d' ${remote_filename} | sed '$d' | sed '$d' > ${output_filename}
echo "    }," >> ${output_filename}
sed "1,2d; $d" ${file_to_append} >> ${output_filename}

pwsh ./powershell/deploy_to_vps.ps1 ${output_filename} ${vps_ip_address}

rm -rf $remote_filename
rm -rf $output_filename



