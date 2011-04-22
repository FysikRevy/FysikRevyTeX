#!/bin/bash

# This file is supposed to be run by the RevyTeX Makefile

REVUE=""
YEAR=""

while [ "$REVUE" = "" ]; do
	echo -n "Enter revue name: "
	read REVUE
done

echo -n "Enter year (enter for $(date +%Y)): "
read YEAR

if [ "$YEAR" = "" ]; then
	YEAR=$(date +%Y)
fi

SCRIPTDIR=$(cd scripts && pwd -P)

sed -i "s~REVUENAME~$REVUE~" `grep -lr "REVUENAME" $1`
sed -i "s~REVUEYEAR~$YEAR~" `grep -lr "REVUEYEAR" $1`
sed -i "s~SCRIPTDIR~$SCRIPTDIR~" `grep -lr "SCRIPTDIR" $1`
