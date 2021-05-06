#! /bin/bash

declare -a symbol_list=("1INCHBTC" "AAVEBTC" "ACMBTC" "ADABTC" "ADXBTC" "AERGOBTC" "AIONBTC" "ALGOBTC" "ALICEBTC" "ALPHABTC" "ANTBTC" "ARDRBTC" "ARKBTC" "ASTBTC" "ATOMBTC" "AUDIOBTC" "AVABTC" "AVAXBTC" "AXSBTC" "BADGERBTC" "BALBTC" "BANDBTC" "BATBTC" "BCDBTC" "BCHBTC" "BELBTC" "BLZBTC" "BNTBTC" "BQXBTC" "BRDBTC" "BTCSTBTC" "BTGBTC" "BZRXBTC" "CAKEBTC" "CELOBTC" "CHRBTC" "CHZBTC" "COMPBTC" "COTIBTC" "CRVBTC" "CTKBTC" "CTSIBTC" "CVCBTC" "DASHBTC" "DCRBTC" "DEGOBTC" "DIABTC" "DNTBTC" "DODOBTC" "DOGEBTC" "DOTBTC" "DUSKBTC" "EASYBTC" "EGLDBTC" "ELFBTC" "ENJBTC" "EOSBTC" "ETCBTC" "EVXBTC" "FETBTC" "FILBTC" "FIOBTC" "FIROBTC" "FISBTC" "FLMBTC" "FRONTBTC" "FTMBTC" "FTTBTC" "FXSBTC" "GASBTC" "GLMBTC" "GRSBTC" "GRTBTC" "GVTBTC" "GXSBTC" "HARDBTC" "HBARBTC" "HIVEBTC" "HNTBTC" "ICXBTC" "INJBTC" "IOTABTC" "JUVBTC" "KAVABTC" "KMDBTC" "KNCBTC" "KSMBTC" "LINKBTC" "LITBTC" "LRCBTC" "LSKBTC" "LTCBTC" "LTOBTC" "LUNABTC" "MANABTC" "MATICBTC" "MDABTC" "MKRBTC" "MTLBTC" "NANOBTC" "NAVBTC" "NEARBTC" "NEBLBTC" "NEOBTC" "NKNBTC" "NMRBTC" "NULSBTC" "NXSBTC" "OCEANBTC" "OGBTC" "OGNBTC" "OMBTC" "OMGBTC" "ONGBTC" "ORNBTC" "OXTBTC" "PAXGBTC" "PHABTC" "PIVXBTC" "PNTBTC" "POLYBTC" "POWRBTC" "PPTBTC" "PSGBTC" "QTUMBTC" "RDNBTC" "RENBTC" "REPBTC" "RIFBTC" "RLCBTC" "RUNEBTC" "SANDBTC" "SCRTBTC" "SFPBTC" "SKLBTC" "SKYBTC" "SNXBTC" "SOLBTC" "SRMBTC" "STEEMBTC" "STORJBTC" "STRAXBTC" "STXBTC" "SUNBTC" "SUSHIBTC" "SXPBTC" "SYSBTC" "TFUELBTC" "THETABTC" "TOMOBTC" "TRBBTC" "TVKBTC" "TWTBTC" "UNFIBTC" "UNIBTC" "UTKBTC" "VIABTC" "VIDTBTC" "WABIBTC" "WANBTC" "WAVESBTC" "WBTCBTC" "WINGBTC" "WNXMBTC" "WRXBTC" "XEMBTC" "XLMBTC" "XMRBTC" "XRPBTC" "XTZBTC" "XVSBTC" "YFIBTC" "YFIIBTC" "ZECBTC" "ZENBTC" "ZRXBTC")

declare -a start_hours_ago=2

declare -a future_flag=""

declare -a moonbot_flag=""

declare -a order_size_mb=0.0002
declare -a order_size_mt=100

now_timestamp="$(date +'%s')"
now_timestamp=$((now_timestamp - now_timestamp % 60))

start_timestamp=$((now_timestamp - 3600 * start_hours_ago))
start_date="$(date -j -f "%s" "${start_timestamp}" "+%Y-%m-%dT%H:%M:%S")"
end_timestamp=$((start_timestamp + 3600 * start_hours_ago))
end_date="$(date -j -f "%s" "${end_timestamp}" "+%Y-%m-%dT%H:%M:%S")"

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

echo Processing shots for the last $start_hours_ago hours:
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
    python calc_shots_pnl_mt.py -e binance -s $symbol $future_flag
done

# Generate strategy files for MB/MT
python strategy_generator.py -e binance -t $order_size_mb -y $order_size_mt $future_flag $moonbot_flag