#! /bin/bash

#declare -a symbol_list=("BTCUSDT" "1INCHUSDT" "AAVEUSDT" "ACMUSDT" "ADAUSDT" "AIONUSDT" "AKROUSDT" "ALGOUSDT" "ALICEUSDT" "ALPHAUSDT" "ANKRUSDT" "ARUSDT" "ASRUSDT" "ATMUSDT" "ATOMUSDT" "AUDIOUSDT" "AVAXUSDT" "AXSUSDT" "BAKEUSDT" "BALUSDT" "BANDUSDT" "BARUSDT" "BATUSDT" "BCHUSDT" "BEAMUSDT" "BELUSDT" "BLZUSDT" "BTTUSDT" "BURGERUSDT" "BZRXUSDT" "CAKEUSDT" "CELOUSDT" "CELRUSDT" "CHZUSDT" "CKBUSDT" "COMPUSDT" "COTIUSDT" "CRVUSDT" "CTKUSDT" "CTSIUSDT" "CVCUSDT" "DASHUSDT" "DEGOUSDT" "DENTUSDT" "DGBUSDT" "DIAUSDT" "DODOUSDT" "DOGEUSDT" "DOTUSDT" "EGLDUSDT" "ENJUSDT" "EOSUSDT" "EPSUSDT" "ETCUSDT" "FETUSDT" "FILUSDT" "FLMUSDT" "FTMUSDT" "FTTUSDT" "GRTUSDT" "GXSUSDT" "HARDUSDT" "HBARUSDT" "HOTUSDT" "ICPUSDT" "ICXUSDT" "INJUSDT" "IOSTUSDT" "IOTAUSDT" "IOTXUSDT" "IRISUSDT" "JUVUSDT" "KAVAUSDT" "KNCUSDT" "KSMUSDT" "LAZIOUSDT" "LINAUSDT" "LINKUSDT" "LITUSDT" "LRCUSDT" "LSKUSDT" "LUNAUSDT" "MANAUSDT" "MATICUSDT" "MDXUSDT" "MFTUSDT" "MITHUSDT" "MKRUSDT" "NANOUSDT" "NEARUSDT" "NEOUSDT" "NKNUSDT" "OCEANUSDT" "OGNUSDT" "OGUSDT" "OMGUSDT" "OMUSDT" "ONEUSDT" "ONTUSDT" "OXTUSDT" "PERPUSDT" "PONDUSDT" "PSGUSDT" "PUNDIXUSDT" "QTUMUSDT" "REEFUSDT" "RENUSDT" "RLCUSDT" "RSRUSDT" "RUNEUSDT" "RVNUSDT" "SANDUSDT" "SCUSDT" "SFPUSDT" "SHIBUSDT" "SKLUSDT" "SLPUSDT" "SNXUSDT" "SOLUSDT" "SRMUSDT" "STMXUSDT" "STORJUSDT" "STRAXUSDT" "SUSHIUSDT" "SXPUSDT" "TFUELUSDT" "THETAUSDT" "TKOUSDT" "TLMUSDT" "TOMOUSDT" "TRBUSDT" "TRXUSDT" "TWTUSDT" "UNFIUSDT" "UNIUSDT" "UTKUSDT" "VETUSDT" "VITEUSDT" "VTHOUSDT" "WAVESUSDT" "WINUSDT" "WRXUSDT" "WTCUSDT" "XEMUSDT" "XLMUSDT" "XMRUSDT" "XRPUSDT" "XTZUSDT" "XVSUSDT" "YFIIUSDT" "YFIUSDT" "ZECUSDT" "ZENUSDT" "ZILUSDT" "ZRXUSDT")
#declare -a symbol_list=("1INCHBTC" "AAVEBTC" "ACMBTC" "ADABTC" "AIONBTC" "AKROBTC" "ALGOBTC" "ALICEBTC" "ALPHABTC" "ANKRBTC" "ARBTC" "ASRBTC" "ATMBTC" "ATOMBTC" "AUDIOBTC" "AVAXBTC" "AXSBTC" "BAKEBTC" "BALBTC" "BANDBTC" "BARBTC" "BATBTC" "BCHBTC" "BEAMBTC" "BELBTC" "BLZBTC" "BTTBTC" "BURGERBTC" "BZRXBTC" "CAKEBTC" "CELOBTC" "CELRBTC" "CHZBTC" "CKBBTC" "COMPBTC" "COTIBTC" "CRVBTC" "CTKBTC" "CTSIBTC" "CVCBTC" "DASHBTC" "DEGOBTC" "DENTBTC" "DGBBTC" "DIABTC" "DODOBTC" "DOGEBTC" "DOTBTC" "EGLDBTC" "ENJBTC" "EOSBTC" "EPSBTC" "ETCBTC" "FETBTC" "FILBTC" "FLMBTC" "FTMBTC" "FTTBTC" "GRTBTC" "GXSBTC" "HARDBTC" "HBARBTC" "HOTBTC" "ICPBTC" "ICXBTC" "INJBTC" "IOSTBTC" "IOTABTC" "IOTXBTC" "IRISBTC" "JUVBTC" "KAVABTC" "KNCBTC" "KSMBTC" "LINABTC" "LINKBTC" "LITBTC" "LRCBTC" "LSKBTC" "LUNABTC" "MANABTC" "MATICBTC" "MDXBTC" "MFTBTC" "MITHBTC" "MKRBTC" "NANOBTC" "NEARBTC" "NEOBTC" "NKNBTC" "OCEANBTC" "OGNBTC" "OGBTC" "OMGBTC" "OMBTC" "ONEBTC" "ONTBTC" "OXTBTC" "PERPBTC" "PONDBTC" "PSGBTC" "PUNDIXBTC" "QTUMBTC" "REEFBTC" "RENBTC" "RLCBTC" "RSRBTC" "RUNEBTC" "RVNBTC" "SANDBTC" "SCBTC" "SFPBTC" "SHIBBTC" "SKLBTC" "SLPBTC" "SNXBTC" "SOLBTC" "SRMBTC" "STMXBTC" "STORJBTC" "STRAXBTC" "SUSHIBTC" "SXPBTC" "TFUELBTC" "THETABTC" "TKOBTC" "TLMBTC" "TOMOBTC" "TRBBTC" "TRXBTC" "TWTBTC" "UNFIBTC" "UNIBTC" "UTKBTC" "VETBTC" "VITEBTC" "VTHOBTC" "WAVESBTC" "WINBTC" "WRXBTC" "WTCBTC" "XEMBTC" "XLMBTC" "XMRBTC" "XRPBTC" "XTZBTC" "XVSBTC" "YFIIBTC" "YFIBTC" "ZECBTC" "ZENBTC" "ZILBTC" "ZRXBTC")

declare -a excluded_symbols_regex="BTCUSDT BTCSTUSDT BNBUSDT ETHUSDT LTCUSDT XRPUSDT TUSDUSDT GBPUSDT EURUSDT BUSDUSDT"

python get_symbols.py -q USDT

declare -a symbol_list
while read line; do
    symbol_list+=($line)
done < symbols_spot_usdt.txt

declare -a start_minutes_ago=$((12*60))

declare -a ultrashortmode=${1}

declare -a future_flag=""

declare -a moonbot_flag=""

now_timestamp="$(date +'%s')"
now_timestamp=$((now_timestamp - now_timestamp % 60))

start_timestamp=$((now_timestamp - 60 * start_minutes_ago))
start_date="$(date -j -f "%s" "${start_timestamp}" "+%Y-%m-%dT%H:%M:%S")"
end_timestamp=$((start_timestamp + 60 * start_minutes_ago))
end_date="$(date -j -f "%s" "${end_timestamp}" "+%Y-%m-%dT%H:%M:%S")"

output_folder_prefix="$(date -j -f "%s" "${end_timestamp}" "+%Y%m%d_%H%M")"
BASE_OUT_FOLDER=/Users/alex/Cloud@Mail.Ru/_TEMP/scalping/out/strategies
output_folder="${BASE_OUT_FOLDER}/${output_folder_prefix}_Spot_${start_minutes_ago}m/"

if [ -d "/Users/alex/opt/anaconda3" ]; then
    source /Users/alex/opt/anaconda3/etc/profile.d/conda.sh
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

echo Detecting shots for the last $start_minutes_ago minutes:
echo $start_date
echo $end_date

for symbol in "${symbol_list[@]}"
do
    if printf "${excluded_symbols_regex}" | grep -q ${symbol}; then
        echo Skipping excluded symbol: ${symbol} ...
            continue
    fi
    # Download tick trade data for all symbols
    python binance_trade_data.py -s $symbol -t $start_date -e $end_date $future_flag

    # Detect shots information for all symbols
    python shots_detector.py ${ultrashortmode} -e binance -s $symbol $future_flag $moonbot_flag

    # Calculate best PnL for all the shots
    python calc_shots_pnl.py ${ultrashortmode} -e binance -s $symbol $future_flag $moonbot_flag
done

# Generate strategy files for MB/MT
cd ..
python -m scalping.strategy_generator -e binance $future_flag $moonbot_flag
cd scalping

mkdir $output_folder
cp ./../marketdata/shots/binance/spot/* $output_folder/
cp ./../marketdata/shots/binance/spot/algorithms.config_spot $output_folder/../

# Merge Spot and Future MT strategy files if there are any
./merge_mt_strategies.sh

cp ${BASE_OUT_FOLDER}/algorithms.config_future_spot $output_folder/