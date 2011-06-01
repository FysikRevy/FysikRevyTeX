#!/usr/bin/perl
use strict;
use warnings;
use POSIX;

use JSON::XS;
use File::Slurp;
use Data::Dumper;

binmode STDOUT, ":utf8";

if (!$ARGV[0]) {
        print "Usage: ./props.pl <FILEPATH>\n\n<FILEPATH> must be the revue json file generated from data.pl.\n";
        exit 0;
}

my $revue = decode_json(File::Slurp::read_file($ARGV[0]));

my $act;
my $material;
my $prop;

print '
\documentclass[a4paper,11pt,oneside]{article}
\usepackage[left=0cm,top=0cm,right=0cm,nohead,nofoot]{geometry}
\usepackage{a4wide}
\usepackage{tabularx}
\usepackage{charter,euler}
\usepackage[danish]{babel,varioref}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\frenchspacing
\usepackage{longtable}
\newcommand{\titel}[1]{\hline \multicolumn{3}{|l|}{\textbf{#1}} \\\\ \hline}
\title{Rekvisitliste}
\pagenumbering{arabic}

\textwidth 190mm
\textheight 270mm
\evensidemargin 0pt
\oddsidemargin -15mm
\topmargin -2cm
\headsep 0.5cm

\begin{document}

\maketitle

\setlength\LTleft{0pt}
\setlength\LTright{0pt}
';

foreach $act (@{$revue->{acts}}) {
	print "\n\n".'\begin{longtable}{|p{7cm}|p{4cm}|p{7cm}|}'."\n";

	print '\hline'."\n";
	print '\textbf{'. $act->{title} .'} & Ansvarlig & Status \\\\'."\n";
	print '\endfirsthead'."\n\n";

	print '\hline'."\n";
	print '\textbf{'. $act->{title} .' (fortsat)} & Ansvarlig & Status  \\\\'."\n";
	print '\endhead'."\n\n";

	print '\hline \endfoot'."\n";

	foreach $material (@{$act->{materials}}) {
		print "\n".'\titel{'. $material->{title} .'}'."\n";
		foreach $prop (@{$material->{props}}) {
			print '\textbf{'. $prop->{name} .'} & '. $prop->{responsible} .' & \\\\ '. $prop->{description} .' & & \\\\ \hline'. "\n";
		}
	}

	print '\end{longtable}'."\n\n";
}

print '
\end{document}';
