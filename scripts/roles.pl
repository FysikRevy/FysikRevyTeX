#!/usr/bin/perl
use strict;
use warnings;
use POSIX;

use JSON::XS;
use File::Slurp;
use Data::Dumper;

binmode STDOUT, ":utf8";

if (!$ARGV[0]) {
        print "Usage: ./roles.pl <FILEPATH>\n\n<FILEPATH> must be the revue json file generated from data.pl.\n";
        exit 0;
}

my $revue = decode_json(File::Slurp::read_file($ARGV[0]));

my $act;
my $material;
my $role;

my $pad = 0;
my @actors;

# Find the longest title for pretty printing the tex table
# Also get all actor names while we are at it
foreach $act (@{$revue->{acts}}) {
	foreach $material (@{$act->{materials}}) {
		$pad = length($material->{title}) if (length($material->{title}) > $pad);
		foreach $role (@{$material->{roles}}) {
			push @actors, $role->{actor};
		}
	}
}
$pad += 2;

# Now sort the array and make each actor entry unique
my %saw;
@actors = sort(grep(!$saw{$_}++, @actors));

print '\documentclass[landscape,a3paper]{article}
\usepackage{revy}
\usepackage[danish]{babel}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage[a3paper]{geometry} 

\frenchspacing

\title{\large{Rolleoversigt}}
\revyname{'. $revue->{name} .'}
\revyyear{'. $revue->{year} .'}
\version{'. strftime("%Y-%m-%d", localtime(time)) .'}

\textwidth 360mm
\textheight 260mm

\evensidemargin 0pt
\oddsidemargin 0pt

\headsep 1cm


\renewcommand{\baselinestretch}{1.0}
\newcommand{\q}{\rule{5.5mm}{0mm}}

\newcommand{\actor}[1]{\rotatebox{90}{#1\ }}
\def\makeatactive{\catcode`\@=\active}
\newcount\savedcat
{\makeatactive\catcode`\|=\active\global\let|\ignorespaces
\gdef\actors{\makeatactive\savedcat=\the\catcode`\|\catcode`\|=\active\@actors}
\long\gdef\@actors#1{#1@@\makeatother\catcode`\|=\savedcat}
\gdef@#1@{\def\tempa{}\def\tempb{#1}\ifx\tempa\tempb
\let\next\relax\else\def\next{&\actor{#1}@}\fi\next}}



\begin{document}
\begin{center}

\maketitle

\begin{tabular}{|rl|*{'. (@actors+2) .'}{@{}c@{}|}}
\hline

&Sketch / Navn
';


# Print persons
print '\actors{';
for (my $i = 0; $i < (@actors); $i++) {
	print "\n". sprintf('     %-'.$pad.'s', '');
	for (my $j = 0; $j < $i; $j++) {
		print '|   ';
	}
	print '@'. $actors[$i];
}
print '}\\\\\hline';

foreach $act (@{$revue->{acts}}) {
	print '\multicolumn{'. (@actors+2) .'}{|l|}{\textbf{'. $act->{title} .'}}\\\\'."\n";
	print '\hline'."\n";

	for (my $i = 0, my @materials = @{$act->{materials}}; $i < (@materials); $i++) {
		print sprintf("\n%2d & %-".$pad."s", $i+1, $materials[$i]->{title});
		my %actorrole;
		foreach $role (@{$materials[$i]->{roles}}) {
			$actorrole{$role->{actor}} = $role->{abbr};
		}
		for (my $j = 0; $j < (@actors); $j++) { 
			print sprintf("&%3s", (@actorrole{$actors[$j]} || "\\q"));
		}
		print '\\\\\hline';
        }
}

print '
\end{tabular}
\end{center}
\end{document}
';
