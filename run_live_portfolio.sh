#! /bin/bash

NUMBER_OF_BOTS=$1
PROCESS_DELAY_SECONDS=30

run_bot_process() {
    _botid=${1}
    echo Launching a BacktraderBot instance: BotID=${_botid}
    ./run_bot.sh $_botid $NUMBER_OF_BOTS > ./bot_logs/bot_process_${_botid}.log &
    sleep $PROCESS_DELAY_SECONDS
}

cleanup() {
    kill -9 $(pgrep -f run_bot)
    kill -9 $(pgrep -f bot.backtraderbot)
}

delete_logs(){
    dtime=`date "+%Y%m%d-%H%M%S"`
    mkdir ./bot_logs/backup/${dtime}
    cp ./bot_logs/*.log ./bot_logs/backup/${dtime}
    rm -rf ./bot_logs/*.log
}

if [ "$#" -ne 1 ]; then
    echo "Usage: run_live_portfolio.sh <NUMBER OF BOTS>"
    exit 0
fi

if [ "$1" == "stop" ]; then
    echo "Stopping all BacktraderBot instances.."
    cleanup
    echo "Done!"
    exit 0
fi

cleanup
delete_logs

for (( i=1; i<=${NUMBER_OF_BOTS}; i++ ))
do
     botid=$(printf "%03d" $i)
     run_bot_process bot_${botid}
done
