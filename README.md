**FysikRevyTeX** is the TeXing system used to create the manuscript for FysikRevy&trade;. It is based on the fantastic [RevyTeX][], but adapted to be more physicist-friendly. Right now, the main features over [RevyTeX][] are:

* Completely rewritten in Python 3.
* The manuscript has the traditional front page.

[revytex]: https://github.com/dikurevy/RevyTeX

## Set up instructions
FysikRevyTeX have only very few dependencies:

* Python 3.3 and above.
* [PyPDF2][] for the PDF magic.

When dependencies are met, just put the contents of FysikRevyTeX in a directory of your choice. No installation is required.

FysikRevyTeX has been tested on Linux with Python 3.3 and PyPDF2 v. 1.20.

[pypdf2]: https://pypi.python.org/pypi/PyPDF2

## Usage
### Creating a new revue directory
The FysikRevyTex directory itself is not meant to be touched at any time (except for development). Instead, you need to set up a new directory for your revue:

    $ cd FysikRevyTeX/
    $ python setup.py path/to/directory

where `path/to/directory` should be where you want to set up the revue directory, e.g. `../2014`. 

Enter your newly created directory (`cd path/to/directory`) and do the following:

#### 1. Create TeX files
TeX files for songs and sketches should go into the directories `sange` and `sketches`, respectively. If you need to create the files, look at the templates in the `templates` directory.

#### 2. Create a new plan file
A plan file stores the "layout" of the revue. To create a default file, run

    $ python create.py plan

The plan file `aktoversigt.plan` is created in the directory. Open the file with your favourite text editor and change the order of the material to match the order it appears in the revue. Also delete the section headings *Sange* and *Sketches* and add you own (e.g. *Akt 1*, *Akt 2* etc.).

An example of a plan file could be:

    Akt 1
    sketches/intro.tex
    sange/kondoeffekt.tex

    Akt 2
    sange/kvanter_i_maaneskin.tex
    sketches/find_holger.tex

    Akt 3
    sange/konstantens_klagesang.tex

    Ekstranumre
    sange/oppenheimerstyle.tex


#### 3. Edit configuration (optional)
FysikRevyTeX can be configured by editing the file `revytex.conf`. This is also where properties of the front page can be changed.

#### 4. Rejoice!
You should have a fully working FysikRevyTeX system! See **Day-to-day usage** for instructions on how to use FysikRevyTeX.


### Day-to-day usage
Once FysikRevyTeX has been set up, all interactions with it happens through `create.py`. This is the script to use for creating the full manuscript.

To use it, run the file with an optional argument:

    $ python create.py argument

The possible arguments are described below, and more than one argument can be specified at a time.

#### `python create.py` or `python create.py manus`
Creates the whole manuscript. Look for `manuskript.pdf` in the `pdf/` directory.

#### `python create.py aktoversigt`
Creates the act outline (a "table of contents") for the revue. Look for `aktoversigt.pdf` in the `pdf/` directory.

#### `python create.py roles`
Creates the role/sketch matrix. Look for `rolleliste.pdf` in the `pdf/` directory.

#### `python create.py props`
Creates the list of props. Look for `rekvisitliste.pdf` in the `pdf/` directory.

#### `python create.py frontpage`
Creates the front page for the manuscript. Look for `frontpage.pdf` in the `pdf/` directory.

#### `python create.py material`
Creates PDFs of all songs and sketches. Look for them in the `sange/` and `sketches/` directories.

#### `python create.py individual`
Creates PDFs for each actor containing only the sketches and songs the actor participates in. Look for the file in the `pdf/individuals` directory.
