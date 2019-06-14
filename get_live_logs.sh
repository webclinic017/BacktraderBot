#! /bin/bash

rsync -v -a  --exclude='backup' --include='*' -e ssh alex@159.69.10.75:/home/alex/BacktraderBot/bot_logs/ ./bot_logs/