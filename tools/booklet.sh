#!/bin/sh

pdftk $1 cat 16 1 15S 2S 14 3 13S 4S 12 5 11S 6S 10 7 9S 8S output __temp__.pdf
pdfnup __temp__.pdf --outfile $1.booklet.pdf
rm __temp__.pdf
