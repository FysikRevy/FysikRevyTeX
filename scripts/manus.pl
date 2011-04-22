#!/usr/bin/perl
use strict;
use warnings;
use POSIX;

use JSON::XS;
use File::Slurp;
use Makefile::Parser;
use PDF::Reuse;
use Data::Dumper;

if (!$ARGV[0] || !$ARGV[1]) {
        print "Usage: ./individual.pl <MAKEFILE> <DATAFILE>\n\n<DATAFILE> must be the revue json file generated 
from data.pl.\n";
        exit 0;
}

my $parser = Makefile::Parser->new;
my $make = $parser->parse($ARGV[0]) or die Makefile::Parser->error;
my $revue = decode_json(File::Slurp::read_file($ARGV[1]));

my $act;
my $material;

my $pdf;
my $pagecount = 0;

prFile($make->var('manus'));
prFontSize(24);

prBookmark({
	text => 'Forside',
	act => "$pagecount, 0, 0"
});

prText(292, 700, 'Manuskript', 'center');
prText(292, 660, $revue->{name}.' '.$revue->{year}, 'center');
prText(292, 620, "Skuespiller: _______________________", 'center');

prPage();	
$pagecount = 1;

prBookmark({
	text => 'Aktoversigt',
	act => "$pagecount, 0, 0"
});
$pagecount += prDoc($make->var('acts'));

prBookmark({
	text => 'Rolleoversigt',
	act => "$pagecount, 0, 0"
});
$pagecount += prDoc($make->var('roles'));

my $materialCount = 0;
my $offset = 100;
prFontSize(12);

foreach $act (@{$revue->{acts}}) {
	my $actPageCount = $pagecount;
	my @materials;

	my $size = prStrWidth($act->{'title'}) + 8;
#	print "$size \n\n";

#	prText($offset + 4, 822, $act->{'title'});
#	prAdd("$offset 818 $size 24 re\n0.5 0.5 0.5 rg\nb\n");
	$offset += $size;

	foreach $material (@{$act->{materials}}) {
		$materialCount++;
		push @materials, {
        		text => "$materialCount - $material->{'title'}",
		        act => "$pagecount, 0, 0"
		};

		$pdf = $material->{'location'};
		$pdf =~ s/\.tex$/.pdf/;
		$pagecount += prDoc($pdf);
	}

	prBookmark({
		text => $act->{'title'},
		act => "$actPageCount, 0, 0",
		kids => \@materials
	});
}

prBookmark({
	text => 'Kontaktliste',
	act => "$pagecount, 0, 0"
});
$pagecount += prDoc($make->var('contacts'));

prEnd();
