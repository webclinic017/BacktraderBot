#! /bin/bash

declare -a symbol_list=("1INCHUSDT" "AAVEUSDT" "ACMUSDT" "ADAUSDT" "AIONUSDT" "AKROUSDT" "ALGOUSDT" "ALICEUSDT" "ALPHAUSDT" "ANKRUSDT" "ARUSDT" "ASRUSDT" "ATMUSDT" "ATOMUSDT" "AUDIOUSDT" "AVAXUSDT" "AXSUSDT" "BAKEUSDT" "BALUSDT" "BANDUSDT" "BARUSDT" "BATUSDT" "BCHUSDT" "BEAMUSDT" "BELUSDT" "BLZUSDT" "BTTUSDT" "BURGERUSDT" "BZRXUSDT" "CAKEUSDT" "CELOUSDT" "CELRUSDT" "CHZUSDT" "CKBUSDT" "COMPUSDT" "COTIUSDT" "CRVUSDT" "CTKUSDT" "CTSIUSDT" "CVCUSDT" "DASHUSDT" "DEGOUSDT" "DENTUSDT" "DGBUSDT" "DIAUSDT" "DODOUSDT" "DOGEUSDT" "DOTUSDT" "EGLDUSDT" "ENJUSDT" "EOSUSDT" "EPSUSDT" "ETCUSDT" "FETUSDT" "FILUSDT" "FLMUSDT" "FTMUSDT" "FTTUSDT" "GRTUSDT" "GXSUSDT" "HARDUSDT" "HBARUSDT" "HOTUSDT" "ICPUSDT" "ICXUSDT" "INJUSDT" "IOSTUSDT" "IOTAUSDT" "IOTXUSDT" "IRISUSDT" "JUVUSDT" "KAVAUSDT" "KNCUSDT" "KSMUSDT" "LINAUSDT" "LINKUSDT" "LITUSDT" "LRCUSDT" "LSKUSDT" "LUNAUSDT" "MANAUSDT" "MATICUSDT" "MFTUSDT" "MITHUSDT" "MKRUSDT" "NANOUSDT" "NEARUSDT" "NEOUSDT" "NKNUSDT" "OCEANUSDT" "OGNUSDT" "OGUSDT" "OMGUSDT" "OMUSDT" "ONEUSDT" "ONTUSDT" "OXTUSDT" "PERPUSDT" "PONDUSDT" "PSGUSDT" "PUNDIXUSDT" "QTUMUSDT" "REEFUSDT" "RENUSDT" "RLCUSDT" "RSRUSDT" "RUNEUSDT" "RVNUSDT" "SANDUSDT" "SCUSDT" "SFPUSDT" "SHIBUSDT" "SKLUSDT" "SLPUSDT" "SNXUSDT" "SOLUSDT" "SRMUSDT" "STMXUSDT" "STORJUSDT" "STRAXUSDT" "SUSHIUSDT" "SXPUSDT" "TFUELUSDT" "THETAUSDT" "TKOUSDT" "TLMUSDT" "TOMOUSDT" "TRBUSDT" "TRXUSDT" "TWTUSDT" "UNFIUSDT" "UNIUSDT" "UTKUSDT" "VETUSDT" "VITEUSDT" "VTHOUSDT" "WAVESUSDT" "WINUSDT" "WRXUSDT" "WTCUSDT" "XEMUSDT" "XLMUSDT" "XMRUSDT" "XRPUSDT" "XTZUSDT" "XVSUSDT" "YFIIUSDT" "YFIUSDT" "ZECUSDT" "ZENUSDT" "ZILUSDT" "ZRXUSDT")

declare -a start_minutes_ago=60

declare -a future_flag=""

declare -a moonbot_flag=""

declare -a order_size_mb=0.0002
declare -a order_size_mt=40

now_timestamp="$(date +'%s')"
now_timestamp=$((now_timestamp - now_timestamp % 60))

start_timestamp=$((now_timestamp - 60 * start_minutes_ago))
start_date="$(date -j -f "%s" "${start_timestamp}" "+%Y-%m-%dT%H:%M:%S")"
end_timestamp=$((start_timestamp + 60 * start_minutes_ago))
end_date="$(date -j -f "%s" "${end_timestamp}" "+%Y-%m-%dT%H:%M:%S")"

output_folder_prefix="$(date -j -f "%s" "${end_timestamp}" "+%Y%m%d_%H%M")"
output_folder="/Users/alex/Cloud@Mail.Ru/_TEMP/scalping/out/strategies/${output_folder_prefix}_Spot_${start_minutes_ago}m"

if [ -d "/opt/anaconda3" ]; then
    source /opt/anaconda3/etc/profile.d/conda.sh
elif [ -d "/home/alex/anaconda3" ]; then
    source /home/alex/anaconda3/etc/profile.d/conda.sh
elif [ -d "/Users/alex/anaconda3" ]; then
    source /Users/alex/anaconda3/etc/profile.d/conda.sh
fi
conda activate Backtrader

echo Deleting old data files...
rm -rf ./../marketdata/shots/binance/spot/*
rm -rf ./../marketdata/tradedata/binance/spot/*
echo Done!

echo Processing shots for the past $start_minutes_ago minutes:
echo $start_date
echo $end_date

# Download tick trade data for all symbols
for symbol in "${symbol_list[@]}"
do
    python binance_trade_data.py -s $symbol -t $start_date -e $end_date $future_flag
done

# Detect shots information for all symbols
for symbol in "${symbol_list[@]}"
do
    python shots_detector.py -e binance -s $symbol $future_flag $moonbot_flag
done

# Calculate best PnL for all the shots
for symbol in "${symbol_list[@]}"
do
    python calc_shots_pnl.py -e binance -s $symbol $future_flag $moonbot_flag
done

# Generate strategy files for MB/MT
python strategy_generator.py -e binance -t $order_size_mb -y $order_size_mt $future_flag $moonbot_flag

mkdir $output_folder
cp ./../marketdata/shots/binance/spot/* $output_folder/
cp ./../marketdata/shots/binance/spot/algorithms.config_spot $output_folder/../

BASE_OUT_FOLDER=/Users/alex/Cloud@Mail.Ru/_TEMP/scalping/out/strategies
FILE1=$BASE_OUT_FOLDER/algorithms.config_future
FILE2=$BASE_OUT_FOLDER/algorithms.config_spot
OUTFILE=$BASE_OUT_FOLDER/algorithms.config_future_spot

if [[ -f "$FILE1" && -f "$FILE2" ]]; then
    echo "Merging $FILE2 into the $FILE1 file..."
else
    echo "Files ${FILE1}/${FILE2} missing. Quitting."
    exit 0
fi

sed '$d' $FILE1 | sed '$d' | sed '$d' > $OUTFILE
echo "    }," >> $OUTFILE
sed "1,2d; $d" $FILE2 >> $OUTFILE

echo "Merging done! File $OUTFILE has been created."