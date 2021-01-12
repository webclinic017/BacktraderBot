#! /bin/bash

chmod 744 ./run_*

./run_WFOStep1.sh $1
./run_WFOStep2.sh $1
./run_WFOStep3.sh $1
