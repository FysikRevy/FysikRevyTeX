#!/usr/bin/perl
use strict;
use warnings;
use POSIX;

use Makefile::Parser;
use Text::vCard;
use Text::vCard::Addressbook;
use Data::Dumper;

if (!$ARGV[0]) {
        print "Usage: ./contacts.pl <CONTACTDIR>\n\n<CONTACTDIR> must be a directory containing one or more vCards.\n";
        exit 0;
}

my $parser = Makefile::Parser->new;

my @files = <$ARGV[0]/*.vcf>;
my $abook = Text::vCard::Addressbook->load( \@files );

print '
\documentclass[a4paper,9pt,oneside]{article}
\usepackage[left=0cm,top=1cm,right=0cm,nohead,nofoot]{geometry}
\usepackage{charter,euler}
\usepackage[danish]{babel,varioref}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{longtable}
\pdfminorversion=4
\begin{document}

%\evensidemargin 0pt
%\oddsidemargin 0pt

%\setlength\LTleft{0pt}
%\setlength\LTright{0pt}

\begin{longtable}{|l|l|l|l|}
	\hline
	\textbf{Navn} & \textbf{Nick} & \textbf{Telefon} & \textbf{Email} \\
	\endfirsthead

	\hline
	\textbf{Navn} & \textbf{Nick} & \textbf{Telefon} & \textbf{Email} \\
	\endhead

	\hline
	\endfoot

';

foreach my $vcard ($abook->vcards()) {
	my $name = $vcard->fullname();
	my $nick = ($vcard->get_simple_type('NICKNAME') || '');
	my $tel = ($vcard->get_simple_type('tel') || '');
	my $mail = ($vcard->get_simple_type('email') || '');

	$nick =~ s/([_^])/\\$1/g;
	$tel =~ s/\+45 //;
	$tel =~ s/(\d{2})/$1 /g;
	$mail =~ s/([_^])/\\$1/g;

	print "\\hline $name & $nick & $tel & $mail \\\\\n";
}

print '\end{longtable}';
print '\end{document}';
