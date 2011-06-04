#!/bin/bash

pages=`pdftk $1 dump_data output | grep NumberOfPages | grep -oP "\d+"`
pages=`echo "$pages + ((4 - ($pages % 4)) % 4)" | bc`
args=""

for (( i = 0; i <= $pages/2-1; i++ ))
do
	s1=`expr $pages - $i`
	s2=`expr $i + 1`

	if (( i % 2 == 0)); then
		args="$args $s1 $s2"
	else
		args="$args ${s1}S ${s2}S"
	fi
done

pdftk $1 cat $args output - | pdfnup --outfile ${1}.booklet.pdf
