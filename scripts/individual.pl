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
        print "Usage: ./individual.pl <MAKEFILE> <DATAFILE>\n\n<DATAFILE> must be the revue json file generated from 
data.pl.\n";
        exit 0;
}

my $parser = Makefile::Parser->new;
my $make = $parser->parse($ARGV[0]) or die Makefile::Parser->error;
my $revue = decode_json(File::Slurp::read_file($ARGV[1]));

my $act;
my $material;
my $role;

my %actors;
my $actor;
my $pdf;
my $pagecount = 0;

# Also get all actor names while we are at it
foreach $act (@{$revue->{acts}}) {
	foreach $material (@{$act->{materials}}) {
		foreach $role (@{$material->{roles}}) {
			if (!$actors{$role->{actor}}) {
				$actors{$role->{actor}} = [];
			}
			push(@{$actors{$role->{actor}}}, $material);
		}
	}
}

prDocDir($make->var('individualdir'));

foreach $actor (keys %actors) {
	print "$actor: ";
	prFile($actor .'.pdf');
	
	prFontSize(24);

	prBookmark({
		text => 'Forside',
		act => "$pagecount, 0, 0"
	});

	prText(292, 700, 'Manuskript', 'center');
	prText(292, 660, $revue->{name}.' '.$revue->{year}, 'center');
	prText(292, 620, "Skuespiller: $actor", 'center');

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

	foreach $material (@{$actors{$actor}}) {
		$pdf = $material->{'location'};
		$pdf =~ s/\.tex$/.pdf/;

		prBookmark({
			text => $material->{'title'},
			act => "$pagecount, 0, 0"
		});

		$pagecount += prDoc($pdf);
	}

	prBookmark({
		text => 'Kontaktliste',
		act => "$pagecount, 0, 0"
	});
	$pagecount += prDoc($make->var('contacts'));

	prEnd();

	print "OK\n";
}
