#!/usr/bin/perl
use strict;
use warnings;

use Data::Dumper;
use JSON::XS;
use File::Slurp;

#binmode STDOUT, ":encoding(utf8)";

# The acts.plan file path must be supplied as the first argument to the script
my $plan = $ARGV[1];

if (!$plan) {
	print "Usage: ./data.pl <jsonconfig> <plan>\n\n<plan> must be the acts.plan file.\n";
	exit 0;
}
my $revue = decode_json(File::Slurp::read_file($ARGV[0]));
my $currentact;
my $actnumber = 1;
my $materialnumber = 1;

sub newact {
	my $title = shift;
	my %newact = (
		order => $actnumber,
		title => $title || 'File listing',
		length => 0,
		materials => []
	);
	push @{$revue->{acts}}, \%newact;
	$currentact = \%newact;
}

open(FH, $plan) or die ("Could not open $plan");

foreach (<FH>) {
	chomp;
		
	next if (m/^\s*$/); # Empty line, skip

	if (!m/\.tex$/) {
		# New act heading
		&newact($_);
                $actnumber++;
		next;
	} else {
		&newact if (!$currentact);
		my %material = (
			location => $_,
			type => 'sketch',
			order => $materialnumber,
			revuename => '',
			revueyear => '',
			version => '',
			length => 0,
			status => '',
			title => '',
			author => '',
			roles => [],
			props => []
		);

                open(FILE, "<:encoding(utf8)", $_) or die ("Could not open $_");
                foreach (<FILE>) {
			$material{revuename} = $1 if (m/\\revyname\{(.*)\}/);
			$material{revueyear} = $1 if (m/\\revyyear\{(.*)\}/);
			$material{version} = $1 if (m/\\version\{(.*)\}/);
			$material{length} = $1 if (m/\\eta\{.*?(\d+([\.,]\d+)?).*\}/);
			$material{status} = $1 if (m/\\status\{(.*)\}/);
			$material{title} = $1 if (m/\\title\{(.*)\}/);
			$material{author} = $1 if (m/\\author\{(.*)\}/);

			push @{$material{roles}}, {
				title => $3,
				abbr => $1,
				actor => $2
			} if (m/\\role\{(.*?)}\[(.*?)\]\s*(.*?)\s*$/);

			push @{$material{props}}, {
				name => $1,
				responsible => $2,
				description => $3
			} if (m/\\prop\{(.*?)}\[(.*?)\]\s*(.*?)\s*$/);

                        if (m/\\melody\{(.*)\}/) {
				$material{type} = 'song';
       	                        if (m/\\melody\{(.*):.*(?>``|")(.*)(?>''|")}/) {
					$material{composer} = $1;
					$material{melody} = $2;
                                } else {
					$material{melody} = $1;
               	                }
			}
       	        }
                close(FILE);
		
		$material{type} = 'video' if ($material{title} =~ m/^video/i);
		$currentact->{length} += $material{length};

		push @{$currentact->{materials}}, \%material;

		$materialnumber++;
        }
}
close(FH);

#print encode_json $revue
my $coder = JSON::XS->new->utf8->pretty;
print $coder->encode ($revue);
