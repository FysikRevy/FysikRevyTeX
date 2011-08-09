#!/bin/bash

if test $# -lt 1; then
echo "Missing argument: ./booklet.sh <FILENAME>"; exit 0
fi

pages=`pdftk $1 dump_data output | grep NumberOfPages | sed -r "s/.* //g"`
missingpages=`echo "(4 - ($pages % 4)) % 4" | bc`
args=""
blanks=""

pages=`echo "$pages + $missingpages" | bc`

for (( i = 0; i <= ($pages)/2-1; i++ ))
do
	s1=`expr $pages - $i`
	s2=`expr $i + 1`

	if (( i % 2 == 0)); then
		args="$args $s1 $s2"
	else
		args="$args ${s1}S ${s2}S"
	fi
done

for (( i = 0; i< $missingpages; i++ ))
do
    blanks="$blanks B1"
done

pdftk A=$1 B=blank.pdf cat A $blanks output - | pdftk - cat $args output ${1}.temp.pdf
pdfnup --outfile ${1%.pdf}.booklet.pdf ${1}.temp.pdf

rm ${1}.temp.pdf
