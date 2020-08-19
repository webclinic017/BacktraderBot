#! /usr/bin/env zsh

strategy=S004_AlexNoroBandsScalperStrategy
fi_begin="1"
fi_end="3"

if [ -d "/opt/anaconda3" ]; then
    source /opt/anaconda3/etc/profile.d/conda.sh
elif [ -d "/home/alex/anaconda3" ]; then
    source /home/alex/anaconda3/etc/profile.d/conda.sh
elif [ -d "/Users/alex/anaconda3" ]; then
    source /Users/alex/anaconda3/etc/profile.d/conda.sh
fi
conda activate Backtrader

process_run() {
    _file_index=${1}
    echo "---------------------------------------------------------------------------------------------------"
    echo "Running $strategy test #$_file_index"
    current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"

    echo "********** Started: $current_date_time"
    python Random_Market_Price.py -y $strategy -f $_file_index
    current_date_time="`date '+%Y-%m-%d - %H:%M:%S'`"
    echo "********** Finished: $current_date_time"
}

pkill python
pkill python

for file_index in {$fi_begin..$fi_end}
do
    pkill python
    pkill python
    process_run $file_index
done