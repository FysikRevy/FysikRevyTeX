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
	print "Usage: ./individual.pl <MAKEFILE> <DATAFILE>\n\n<DATAFILE> must be the revue json file generated from data.pl.\n";
	exit 0;
}

my $parser = Makefile::Parser->new;
my $make = $parser->parse($ARGV[0]) or die Makefile::Parser->error;
my $revue = decode_json(File::Slurp::read_file($ARGV[1]));

my $act;
my $material;

my $pdf;
my $pagecount = 1;

sub material {
	my $title = shift;
	my $pdf = shift;

	prBookmark({
		text => $title,
		act => "$pagecount, 0, 0"
	});

	prFontSize(10);
	my $left = 1;
	while ($left) {
		$pagecount += 1;
		prText( 550, 30, "Side ".$pagecount, 'right');
		$left = prSinglePage($pdf);
	}
}


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

material('Aktoversigt', $make->var('acts'));
material('Rolleoversigt', $make->var('roles'));

my $materialCount = 0;

foreach $act (@{$revue->{acts}}) {
	my $actPageCount = $pagecount;
	my @materials;

	foreach $material (@{$act->{materials}}) {
		$materialCount++;
		push @materials, {
			text => "$materialCount - $material->{'title'}",
			act => "$pagecount, 0, 0"
		};

		$pdf = $material->{'location'};
		$pdf =~ s/\.tex$/.pdf/;
		my $left = 1;
		while ($left) {
			$pagecount += 1;
			prText( 550, 30, "Side ".$pagecount, 'right');
			$left = prSinglePage($pdf);
		}
	}

	prBookmark({
		text => $act->{'title'},
		act => "$actPageCount, 0, 0",
		kids => \@materials
	});
}

material('Kontaktliste', $make->var('contacts'));

prEnd();
