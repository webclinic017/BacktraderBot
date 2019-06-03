#! /bin/bash

rsync -v -a  --exclude='.git' --exclude='.gitignore' --exclude='.idea' --exclude='*pycache*' --exclude='bot_logs' --exclude='docs' --exclude='marketdata' --exclude='strategyrun_results' --include='*' -e ssh . alex@159.69.10.75:/home/alex/BacktraderBot/