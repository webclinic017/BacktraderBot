#! /bin/bash

declare -a symbol_list=("1INCHBTC" "AAVEBTC" "ACMBTC" "ADABTC" "ADXBTC" "AERGOBTC" "AIONBTC" "ALGOBTC" "ALICEBTC" "ALPHABTC" "ANTBTC" "ARDRBTC" "ARKBTC" "ASTBTC" "ATOMBTC" "AUDIOBTC" "AVABTC" "AVAXBTC" "AXSBTC" "BADGERBTC" "BALBTC" "BANDBTC" "BATBTC" "BCDBTC" "BCHBTC" "BELBTC" "BLZBTC" "BNTBTC" "BQXBTC" "BRDBTC" "BTCSTBTC" "BTGBTC" "BZRXBTC" "CAKEBTC" "CELOBTC" "CHRBTC" "CHZBTC" "COMPBTC" "COTIBTC" "CRVBTC" "CTKBTC" "CTSIBTC" "CVCBTC" "DASHBTC" "DCRBTC" "DEGOBTC" "DIABTC" "DNTBTC" "DODOBTC" "DOGEBTC" "DOTBTC" "DUSKBTC" "EASYBTC" "EGLDBTC" "ELFBTC" "ENJBTC" "EOSBTC" "ETCBTC" "EVXBTC" "FETBTC" "FILBTC" "FIOBTC" "FIROBTC" "FISBTC" "FLMBTC" "FRONTBTC" "FTMBTC" "FTTBTC" "FXSBTC" "GASBTC" "GLMBTC" "GRSBTC" "GRTBTC" "GVTBTC" "GXSBTC" "HARDBTC" "HBARBTC" "HIVEBTC" "HNTBTC" "ICXBTC" "INJBTC" "IOTABTC" "JUVBTC" "KAVABTC" "KMDBTC" "KNCBTC" "KSMBTC" "LINKBTC" "LITBTC" "LRCBTC" "LSKBTC" "LTCBTC" "LTOBTC" "LUNABTC" "MANABTC" "MATICBTC" "MDABTC" "MKRBTC" "MTLBTC" "NANOBTC" "NAVBTC" "NEARBTC" "NEBLBTC" "NEOBTC" "NKNBTC" "NMRBTC" "NULSBTC" "NXSBTC" "OCEANBTC" "OGBTC" "OGNBTC" "OMBTC" "OMGBTC" "ONGBTC" "ORNBTC" "OXTBTC" "PAXGBTC" "PHABTC" "PIVXBTC" "PNTBTC" "POLYBTC" "POWRBTC" "PPTBTC" "PSGBTC" "QTUMBTC" "RDNBTC" "RENBTC" "REPBTC" "RIFBTC" "RLCBTC" "RUNEBTC" "SANDBTC" "SCRTBTC" "SFPBTC" "SKLBTC" "SKYBTC" "SNXBTC" "SOLBTC" "SRMBTC" "STEEMBTC" "STORJBTC" "STRAXBTC" "STXBTC" "SUNBTC" "SUSHIBTC" "SXPBTC" "SYSBTC" "TFUELBTC" "THETABTC" "TOMOBTC" "TRBBTC" "TVKBTC" "TWTBTC" "UNFIBTC" "UNIBTC" "UTKBTC" "VIABTC" "VIDTBTC" "WABIBTC" "WANBTC" "WAVESBTC" "WBTCBTC" "WINGBTC" "WNXMBTC" "WRXBTC" "XEMBTC" "XLMBTC" "XMRBTC" "XRPBTC" "XTZBTC" "XVSBTC" "YFIBTC" "YFIIBTC" "ZECBTC" "ZENBTC" "ZRXBTC")

csv_file=$1

f_counter=1
s_counter=1
max_symbols_file=20

out_file_base="${csv_file%%.*}"

for symbol in "${symbol_list[@]}"
do
    if [[ ${s_counter} -eq 1 ]];
    then
        out_file="${out_file_base}_${f_counter}.csv"
        echo "File: ${out_file}"

        if [[ ${f_counter} -eq 1 ]];
        then
            cat $csv_file | grep "symbol_name" > $out_file
        fi
    fi

    echo "Writing ${symbol} data..."
    cat $csv_file | grep "${symbol}" >> $out_file

    s_counter=$((s_counter + 1))

    if [[ ${s_counter} -gt ${max_symbols_file} ]];
    then
        s_counter=1
        f_counter=$((f_counter + 1))
    fi
done
