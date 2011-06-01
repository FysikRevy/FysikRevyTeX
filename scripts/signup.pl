#!/usr/bin/perl
use strict;
use warnings;
use POSIX;

use JSON::XS;
use File::Slurp;
use Data::Dumper;

binmode STDOUT, ":utf8";

if (!$ARGV[0]) {
        print "Usage: ./signup.pl <FILEPATH>\n\n<FILEPATH> must be the revue json file generated from data.pl.\n";
        exit 0;
}

my $revue = decode_json(File::Slurp::read_file($ARGV[0]));

my $act;
my $material;
my $role;

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
\usepackage{verbatim,moreverb}
\usepackage{multirow}
\usepackage{hhline}
\usepackage{latexsym}
\usepackage{longtable}
\newcommand{\titel}[1]{\hline \multicolumn{5}{|l|}{\textbf{#1}} \\\\ \hline}
\newcommand{\role}[1]{#1 & $\Box$ & $\Box$ & $\Box$  & \rule[-2mm]{5.5cm}{0.1pt} \\\\}
\title{Rolletilmelding}
\pagenumbering{arabic}
\begin{document}

\setlength\LTleft{0pt}
\setlength\LTright{0pt}
';

foreach $act (@{$revue->{acts}}) {
	print "\n\n".'\begin{longtable}{|p{7cm}|cccl|}'."\n";

	print '\hline'."\n";
	print '\textbf{'. $act->{title} .'} & ++ & + & - & Kommentar \\\\'."\n";
	print '\endfirsthead'."\n\n";

	print '\hline'."\n";
	print '\textbf{'. $act->{title} .' (fortsat)} & ++ & + & - & Kommentar \\\\'."\n";
	print '\endhead'."\n\n";

	print '\hline \endfoot'."\n";

	foreach $material (@{$act->{materials}}) {
		print "\n".'\titel{'. $material->{title} .'}'."\n";
		foreach $role (@{$material->{roles}}) {
			print '\role{'. ($role->{title} || $role->{abbr}) .'}'."\n";
		}
	}

	print '\end{longtable}'."\n\n";
}

print '
\end{document}';
