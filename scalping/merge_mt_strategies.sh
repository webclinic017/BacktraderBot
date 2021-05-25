#! /bin/bash

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