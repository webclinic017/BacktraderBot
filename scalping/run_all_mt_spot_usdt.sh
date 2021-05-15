#! /bin/bash

declare -a symbol_list=("1INCHDOWNUSDT" "1INCHUPUSDT" "1INCHUSDT" "AAVEDOWNUSDT" "AAVEUPUSDT" "AAVEUSDT" "ACMUSDT" "ADADOWNUSDT" "ADAUPUSDT" "ADAUSDT" "AIONUSDT" "AKROUSDT" "ALGOUSDT" "ALICEUSDT" "ALPHAUSDT" "ANKRUSDT" "ANTUSDT" "ARDRUSDT" "ARPAUSDT" "ARUSDT" "ASRUSDT" "ATMUSDT" "ATOMUSDT" "AUDIOUSDT" "AUDUSDT" "AUTOUSDT" "AVAUSDT" "AVAXUSDT" "AXSUSDT" "BADGERUSDT" "BAKEUSDT" "BALUSDT" "BANDUSDT" "BARUSDT" "BATUSDT" "BCHDOWNUSDT" "BCHUPUSDT" "BCHUSDT" "BEAMUSDT" "BELUSDT" "BLZUSDT" "BNBDOWNUSDT" "BNBUPUSDT" "BNTUSDT" "BTCDOWNUSDT" "BTCSTUSDT" "BTCUPUSDT" "BTGUSDT" "BTSUSDT" "BTTUSDT" "BURGERUSDT" "BZRXUSDT" "CAKEUSDT" "CELOUSDT" "CELRUSDT" "CFXUSDT" "CHRUSDT" "CHZUSDT" "CKBUSDT" "COCOSUSDT" "COMPUSDT" "COSUSDT" "COTIUSDT" "CRVUSDT" "CTKUSDT" "CTSIUSDT" "CTXCUSDT" "CVCUSDT" "DASHUSDT" "DATAUSDT" "DCRUSDT" "DEGOUSDT" "DENTUSDT" "DGBUSDT" "DIAUSDT" "DNTUSDT" "DOCKUSDT" "DODOUSDT" "DOGEUSDT" "DOTDOWNUSDT" "DOTUPUSDT" "DOTUSDT" "DREPUSDT" "DUSKUSDT" "EGLDUSDT" "ENJUSDT" "EOSDOWNUSDT" "EOSUPUSDT" "EOSUSDT" "EPSUSDT" "ETCUSDT" "ETHDOWNUSDT" "ETHUPUSDT" "FETUSDT" "FILDOWNUSDT" "FILUPUSDT" "FILUSDT" "FIOUSDT" "FIROUSDT" "FISUSDT" "FLMUSDT" "FORTHUSDT" "FTMUSDT" "FTTUSDT" "FUNUSDT" "GBPUSDT" "GRTUSDT" "GTOUSDT" "GXSUSDT" "HARDUSDT" "HBARUSDT" "HIVEUSDT" "HNTUSDT" "HOTUSDT" "ICPUSDT" "ICXUSDT" "INJUSDT" "IOSTUSDT" "IOTAUSDT" "IOTXUSDT" "IRISUSDT" "JSTUSDT" "JUVUSDT" "KAVAUSDT" "KEYUSDT" "KMDUSDT" "KNCUSDT" "KSMUSDT" "LINAUSDT" "LINKDOWNUSDT" "LINKUPUSDT" "LINKUSDT" "LITUSDT" "LRCUSDT" "LSKUSDT" "LTCDOWNUSDT" "LTCUPUSDT" "LTCUSDT" "LTOUSDT" "LUNAUSDT" "MANAUSDT" "MATICUSDT" "MBLUSDT" "MDTUSDT" "MFTUSDT" "MIRUSDT" "MITHUSDT" "MKRUSDT" "MTLUSDT" "NANOUSDT" "NBSUSDT" "NEARUSDT" "NEOUSDT" "NKNUSDT" "NMRUSDT" "NULSUSDT" "OCEANUSDT" "OGNUSDT" "OGUSDT" "OMGUSDT" "OMUSDT" "ONEUSDT" "ONGUSDT" "ONTUSDT" "ORNUSDT" "OXTUSDT" "PAXGUSDT" "PAXUSDT" "PERLUSDT" "PERPUSDT" "PNTUSDT" "PONDUSDT" "PSGUSDT" "PUNDIXUSDT" "QTUMUSDT" "RAMPUSDT" "REEFUSDT" "RENUSDT" "REPUSDT" "RIFUSDT" "RLCUSDT" "ROSEUSDT" "RSRUSDT" "RUNEUSDT" "RVNUSDT" "SANDUSDT" "SCUSDT" "SFPUSDT" "SHIBUSDT" "SKLUSDT" "SLPUSDT" "SNXUSDT" "SOLUSDT" "SRMUSDT" "STMXUSDT" "STORJUSDT" "STPTUSDT" "STRAXUSDT" "STXUSDT" "SUNUSDT" "SUPERUSDT" "SUSDUSDT" "SUSHIDOWNUSDT" "SUSHIUPUSDT" "SUSHIUSDT" "SXPDOWNUSDT" "SXPUPUSDT" "SXPUSDT" "TCTUSDT" "TFUELUSDT" "THETAUSDT" "TKOUSDT" "TLMUSDT" "TOMOUSDT" "TRBUSDT" "TROYUSDT" "TRUUSDT" "TRXDOWNUSDT" "TRXUPUSDT" "TRXUSDT" "TUSDUSDT" "TWTUSDT" "UMAUSDT" "UNFIUSDT" "UNIDOWNUSDT" "UNIUPUSDT" "UNIUSDT" "USDCUSDT" "UTKUSDT" "VETUSDT" "VITEUSDT" "VTHOUSDT" "WANUSDT" "WAVESUSDT" "WINGUSDT" "WINUSDT" "WNXMUSDT" "WRXUSDT" "WTCUSDT" "XEMUSDT" "XLMDOWNUSDT" "XLMUPUSDT" "XLMUSDT" "XMRUSDT" "XRPDOWNUSDT" "XRPUPUSDT" "XRPUSDT" "XTZDOWNUSDT" "XTZUPUSDT" "XTZUSDT" "XVSUSDT" "YFIDOWNUSDT" "YFIIUSDT" "YFIUPUSDT" "YFIUSDT" "ZECUSDT" "ZENUSDT" "ZILUSDT" "ZRXUSDT")

declare -a start_minutes_ago=60

declare -a future_flag=""

declare -a moonbot_flag=""

declare -a order_size_mb=0.0002
declare -a order_size_mt=400

now_timestamp="$(date +'%s')"
now_timestamp=$((now_timestamp - now_timestamp % 60))

start_timestamp=$((now_timestamp - 60 * start_minutes_ago))
start_date="$(date -j -f "%s" "${start_timestamp}" "+%Y-%m-%dT%H:%M:%S")"
end_timestamp=$((start_timestamp + 60 * start_minutes_ago))
end_date="$(date -j -f "%s" "${end_timestamp}" "+%Y-%m-%dT%H:%M:%S")"

output_folder_prefix="$(date -j -f "%s" "${end_timestamp}" "+%Y%m%d_%H%M")"
output_folder="/Users/alex/Cloud@Mail.Ru/_TEMP/scalping/out/strategies/${output_folder_prefix}/"

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

echo Processing shots for the last $start_minutes_ago minutes:
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
cp ./../marketdata/shots/binance/spot/* $output_folder
cp ./../marketdata/shots/binance/spot/algorithms.config $output_folder/../