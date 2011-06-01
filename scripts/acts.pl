#!/usr/bin/perl
use strict;
use warnings;
use POSIX;
use JSON::XS;
use File::Slurp;
binmode STDOUT, ":utf8";

if (!$ARGV[0]) {
        print "Usage: ./acts.pl <FILEPATH>\n\n<FILEPATH> must be the revue json file generated from data.pl.\n";
        exit 0;
}
my $revue = decode_json(File::Slurp::read_file($ARGV[0]));
my $act;
my $material;

print '\documentclass[danish]{article}
\usepackage{revy}
\usepackage{babel}
\usepackage[utf8]{inputenc}
\usepackage{anysize}

\title{Aktoversigt}

\version{'. strftime("%Y-%m-%d", localtime(time)) .'}
\revyname{'. $revue->{name} .'}
\revyyear{'. $revue->{year} .'}

\begin{document}

\maketitle

';

foreach $act (@{$revue->{acts}}) {
	print '\section*{'. $act->{title} .'  \small{\textbf{\emph{(Tidsestimat: '. $act->{length} .' minutter)}}}}'."\n";
	print '\begin{enumerate}'."\n";
        foreach $material (@{$act->{materials}}) {
		print '\item \textbf{'. $material->{title} .'} ';
		if ($material->{composer}) {
			print "($material->{composer}: ``$material->{melody}'') ";
		} elsif ($material->{melody}) {
			print "($material->{melody}) ";
		}
		print '\emph{'. $material->{revuename} .' '. $material->{revueyear} .'} \\\\'."\n";
#		print '\emph{Version '. $material->{version} .'} \\\\'."\n";
		print '\small{Status: '. $material->{status} .', \emph{Tidsestimat: '. $material->{length} .' minutter}}'."\n";
        }
	print '\end{enumerate}'."\n\n";
}

print '\end{document}';

