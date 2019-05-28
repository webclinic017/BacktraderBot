#! /bin/sh

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

run_bot_process bot_001
run_bot_process bot_002
run_bot_process bot_003
run_bot_process bot_004
run_bot_process bot_005
run_bot_process bot_006
run_bot_process bot_007
run_bot_process bot_008
run_bot_process bot_009
run_bot_process bot_010