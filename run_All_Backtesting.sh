#! /bin/bash

chmod 744 ./run_Backtesting*

run_WFOStep1.sh $1
./run_BacktestingStep2.sh $1
./run_BacktestingStep3.sh $1
./run_BacktestingStep4.sh $1
./run_BacktestingStep5.sh $1
