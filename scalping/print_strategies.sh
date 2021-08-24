#! /bin/bash

declare -a filename=~/Downloads/algorithms.config_future
#declare -a filename=/Users/alex/Cloud@Mail.Ru/_TEMP/scalping/out/strategies/algorithms.config_future

ggrep -oP "(?<=\"info\": \").*(?=\")" ${filename}