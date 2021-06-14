#! /bin/bash

#declare -a filename=~/Downloads/algorithms.config
declare -a filename=/Users/alex/Cloud@Mail.Ru/_TEMP/scalping/out/strategies/algorithms.config_future_spot

ggrep -oP "(?<=\"info\": \").*(?=\")" ${filename}