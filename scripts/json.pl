#!/usr/bin/perl
use strict;
use warnings;

use Storable;
use JSON::XS;

if (!$ARGV[0]) {
        print "Usage: ./data2json.pl <FILEPATH>\n\n<FILEPATH> must be the revue data file generated from data.pl.\n";
        exit 0;
}

print 'var data = '. JSON::XS->new->utf8->pretty->encode(retrieve($ARGV[0]));
