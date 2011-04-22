# Makefile configuration for RevyScript
#
# Author: munter@diku.dk
#
# This file should be copied and adapted to your local environment

# Get revue working directory, ignore symlinks
revuedir := $(shell cd . && pwd -P)

# Define where the scripts are placed.
scriptdir := $(shell cd .. && pwd -P)/scripts

# The directories where original .tex materials will be placed
sketchdir := $(revuedir)/sketches
songdir := $(revuedir)/sange
videodir := $(revuedir)/video
bitsdir := $(revuedir)/brokker
contactsdir := $(revuedir)/kontakter

# The acts plan. A cleartext file with act headings and material order
plan := $(revuedir)/aktoversigt.plan

# Define where to place output files
outputdir := $(revuedir)/www

# Where to put the datafile
json := $(outputdir)/json.js

# Auto generated PDF output placements
manus := $(outputdir)/Manuskript.pdf
acts := $(outputdir)/Aktoversigt.pdf
roles := $(outputdir)/Rolleoversigt.pdf
signup := $(outputdir)/Rolletilmelding.pdf
props := $(outputdir)/Rekvisitliste.pdf
contacts := $(outputdir)/Kontaktliste.pdf
individualdir := $(outputdir)/Individuelt
