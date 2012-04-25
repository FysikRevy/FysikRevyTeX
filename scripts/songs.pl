#!/usr/bin/perl
use strict;
use warnings;
use POSIX;

use JSON::XS;
use File::Slurp;
use Makefile::Parser;
use PDF::Reuse;
use Data::Dumper;

binmode STDOUT, ":utf8";

if (!$ARGV[0] || !$ARGV[1]) {
        print "Usage: ./songs.pl <MAKEFILE> <DATAFILE>\n\n<DATAFILE> must be the revue json file generated from 
data.pl.\n";
        exit 0;
}

my $parser = Makefile::Parser->new;
my $make = $parser->parse($ARGV[0]) or die Makefile::Parser->error;
my $revue = decode_json(File::Slurp::read_file($ARGV[1]));

my $act;
my $material;

my @songs;
my $pdf;
my $pagecount = 1;

foreach $act (@{$revue->{acts}}) {
	foreach $material (@{$act->{materials}}) {
        push(@songs, $material) if $material->{type} eq 'song';
	}
}

prFile($make->var('songs'));

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

print "Sangmanuskript: ";

prFontSize(24);

prBookmark({
    text => 'Forside',
    act => "$pagecount, 0, 0"
});

prText(292, 700, 'Sangmanuskript', 'center');
prText(292, 660, $revue->{name}.' '.$revue->{year}, 'center');
prText(292, 620, "Indehaver: _______________________", 'center');

prPage();

foreach $material (@songs) {
    $pdf = $material->{'location'};
    $pdf =~ s/\.tex$/.pdf/;

    material($material->{'title'}, $pdf);
}

prEnd();

print "OK\n";
