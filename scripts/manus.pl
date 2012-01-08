#!/usr/bin/perl
use strict;
use warnings;
use POSIX;

use JSON::XS;
use File::Slurp;
use Makefile::Parser;
use PDF::Reuse;
use PDF::API2::Util;
use Getopt::Long;

my ($help, $contacts, $make, $revue, $outfile);
my $usage = "usage: program [--help|-h] [--contacts] [--outfile FILENAME] --config MAKEFILE --data JSON\n";

if (! GetOptions(
        'help|h' => sub {
            print $usage; exit;
        },
        'contacts' => \$contacts,
        'config=s' => sub {
            $make = Makefile::Parser->new->parse($_[1]) or die Makefile::Parser->error;
        },
        'data=s' => sub {
            $revue = decode_json(File::Slurp::read_file($_[1]));
        },
        'outfile=s' => \$outfile
    )
) {
  print "Unknown option: @_\n" if ( @_ );
  print $usage;
  exit;
};

my $act;
my $material;

my $pdf;
my $pagecount = 1;

use constant WIDTH     => 595.28;
use constant HEIGHT    => 841.89;
use constant FONT_SIZE => 10;

sub rect {
	my ($args) = @_;
	my @c = namecolor($args->{color});

	my $str = "q\n";                                                       # save the graphic state
	$str   .= "$c[0] $c[1] $c[2] rg\n";                                    # a fill color
	$str   .= "$args->{x} $args->{y} $args->{width} $args->{height} re\n"; # a rectangle
	$str   .= "b\n";                                                       # fill (and a little more)
	$str   .= "Q\n";                                                       # restore the graphic state

	prAdd($str);
};

sub prColor {
	my @c = namecolor(shift);
	prAdd("$c[0] $c[1] $c[2] rg");
};

my $taboffset = 85;
my $oldtabtext = '';
my $oldtabwidth = 0;
sub indexTab {
	my ($args) = @_;

	$args->{paddingTop} //= 15;
	$args->{paddingRight} //= 5;
	$args->{paddingBottom} //= 5;
	$args->{paddingLeft} //= 5;

	my $width = prStrWidth( $args->{text}, 'C', FONT_SIZE ) + $args->{paddingRight} + $args->{paddingLeft};
	my $height = FONT_SIZE + $args->{paddingTop} + $args->{paddingBottom};

	if ( $oldtabtext ne $args->{text} ) {
		$taboffset += $oldtabwidth;
		$oldtabtext = $args->{text};
		$oldtabwidth = $width;
	}

	rect({
		color => 'black',
		width => $width,
		height => $height,
		x => $taboffset,
		y => HEIGHT - $height
	});

	prColor('white');
	prFont("C");
	prFontSize(FONT_SIZE);

	prText($taboffset + $args->{paddingLeft}, HEIGHT - $height + $args->{paddingBottom}, $args->{text});

	prColor('black');
};

sub material {
	my ($args) = shift;

	prBookmark({
		text => $args->{title},
		act => "$pagecount, 0, 0"
	});

	prFontSize(10);
	my $left = 1;
	while ($left) {
		indexTab({
			text => $args->{title}
		});
		prText( 550, 30, "Side ".++$pagecount, 'right');
		$left = prSinglePage($args->{pdf});
	}
};

### Document start ###

prFile($outfile);
prFontSize(24);

prBookmark({
	text => 'Forside',
	act => "0, 0, 0"
});

prText(292, 700, 'Manuskript', 'center');
prText(292, 660, $revue->{name}.' '.$revue->{year}, 'center');
prText(292, 620, "Skuespiller: _______________________", 'center');

prPage();

material({
	title => 'Aktoversigt',
	pdf => $make->var('acts')
});

prPage();
prForm({
	file => $make->var('roles'),
	size => (1/sqrt(2)),
	rotate => 90,
	x => WIDTH
});
indexTab({
	text => 'Rolleoversigt'
});
prBookmark({
	text => 'Rolleoversigt',
	act => "$pagecount, 0, 0"
});
prText( 550, 30, "Side ".++$pagecount, 'right');
prPage();

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
			indexTab({
				text => $act->{title}
			});
			$pagecount += 1;
			prText( 550, 30, "Side ".$pagecount, 'right');

			### Material index tab start
			my $height = prStrWidth("$materialCount - $material->{'title'}", 'C', FONT_SIZE ) + 7 + 7;
			my $width = FONT_SIZE + 5 + 5;
			my $x = WIDTH - $width - 10;
			my $y = HEIGHT - (110 + ($materialCount - 1) * 20);

			rect({
				color => 'black',
				width => $width,
				height => $height,
				x => $x,
				y => $y - $height
			});

			rect({
				color => 'black',
				width => 20,
				height => 20,
				x => WIDTH - 15,
				y => $y - 20
			});

			prColor('white');
			prFont("C");
			prFontSize(FONT_SIZE);

			prText($x + 7, $y - 7, "$materialCount - $material->{'title'}", '', 270);

			prColor('black');
			### Material index tab end

			$left = prSinglePage($pdf);
		}
	}

	prBookmark({
		text => $act->{'title'},
		act => "$actPageCount, 0, 0",
		kids => \@materials
	});
}
if ($contacts) {
    material({
    	title => 'Kontaktliste',
    	pdf => $make->var('contacts')
    });
}

prEnd();
