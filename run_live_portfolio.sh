#! /bin/sh

PROCESS_DELAY_SECONDS=30

run_bot_process() {
    _botid=${1}
    sleep $PROCESS_DELAY_SECONDS
    echo Launching a BacktraderBot instance: BotID=${_botid}
    ./run_bot.sh $_botid > ./bot_logs/bot_process_${_botid}.log &
}

kill -- -$(pgrep -f run_bot)
kill -- -$(pgrep -f bot.backtraderbot)

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