**FysikRevyTeX** is the TeXing system used to create the manuscript for FysikRevy&trade;. It is based on the fantastic [RevyTeX][], but adapted to be more physicist-friendly. Right now, the main features over [RevyTeX][] are:

* Completely rewritten in Python 3.
* Parallel generation of PDFs for songs, sketches and individual manuscripts.
* The manuscript has the traditional front page.
> ...mere eller mindre
* The contact list has a more human readable syntax.

[revytex]: https://github.com/dikurevy/RevyTeX

> Og dokumentation på engelsk, hvilket er et valg, som jeg ikke rigtig
> forstår. Men jeg gider ikke skrive det om, så vi nøjes med spydige
> kommentarer på fremmedsprog.

## Set up instructions
FysikRevyTeX has very few dependencies:

* Python 3.3 or newer.
* [PyPDF2][] for the PDF magic.
* [fuzzywuzzy][] til noget tekst-matche-magi

When dependencies are met, just put the contents of FysikRevyTeX in a directory of your choice. No installation is required.

FysikRevyTeX has been tested on Linux with Python 3.3 and PyPDF2 v. 1.20.

> Opdateret og testet på Windows med Python 3.9 og PyPDF2 v. 1.26

[pypdf2]: https://pypi.python.org/pypi/PyPDF2
[fuzzywuzzy]: https://pypi.org/project/fuzzywuzzy/

## Usage
### Creating a new revue directory
The FysikRevyTex directory itself is not meant to be touched at any time (except for development). Instead, you need to set up a new directory for your revue:

    $ cd FysikRevyTeX/
    $ python setup.py path/to/directory

where `path/to/directory` should be where you want to set up the revue directory, e.g. `../2014`. 

Enter your newly created directory (`cd path/to/directory`) and do the following:

#### 1. Create TeX files
TeX files for songs and sketches should go into the directories `sange` and `sketches`, respectively. If you need to create the files, look at the templates in the `templates` directory.

> TeX-filerne kan også bo i undermapper under `sange`- og `sketches`-mapperne. Der er godt nok en risiko for, at LaTeX ikke kan finde `revy.sty` i en undermappe, men det finder du nok ud af at løse ;).

#### 2. Create a new plan file
A plan file defines the "layout" of the revue. To create a default file, run

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

> Listen over tidligere versioner på forsiden er en ny idé, og valgfri. I `.conf`-filen kan værdien `version` enten være en kommasepareret liste over versionsnavne, hvoraf den sidste bliver brugt som den nuværende version, eller kun den nuværende version, hvor listen over tidligere versioner så slet ikke bliver sat på forsiden.

#### 4. Rejoice!
You should have a fully working FysikRevyTeX system! See **Day-to-day usage** for instructions on how to use FysikRevyTeX.


### Day-to-day usage
Once FysikRevyTeX has been set up, all interactions with it happens through `create.py`. This is the script to use for creating the full manuscript.

To use it, run the file with an optional argument:

    $ python create.py argument

The possible arguments are described below, and more than one argument can be specified at a time.

* **`python create.py`** or **`python create.py manus`**<br />
Creates the whole manuscript. Look for `manuskript.pdf` in the `pdf/` directory.

* **`python create.py aktoversigt`**<br />
Creates the act outline (a "table of contents") for the revue. Look for `aktoversigt.pdf` in the `pdf/` directory.

> * **`python create.py thumbindex`**<br />
> Bygger indekssiden til registermærkningerne. Husk, at hvis manuskripsider skal have registermærkninger, så skal `revy.sty` kaldes med argumenterne `thumbindex` og `planfile=`_[stil til planfilen]_. Fx:

    \usepackage[thumbindex,planfile=../aktoversigt.plan]{revy}
    
> **TODO:** Skriv kaldet til `revy` om automatisk.

* **`python create.py roles`**<br />
Creates the role/sketch matrix. Look for `rolleliste.pdf` in the `pdf/` directory.

* **`python create.py props`**<br />
Creates the list of props. Look for `rekvisitliste.pdf` in the `pdf/` directory.

* **`python create.py contacts`**<br />
Creates the contacts list. Look for `kontaktliste.pdf` in the `pdf/` directory.
To add contacts, edit `contacts.csv` with your favourite text editor. 
> Den nye kontaktliste er ikke så fleksibel som den gamle, men den ser bedre ud. _Mike drop_

* **`python create.py songmanus`**<br />
Creates a manuscript containing only songs. Look for `sangmanuskript.pdf` in the `pdf/` directory.

* **`python create.py frontpage`**<br />
Creates the front page for the manuscript. Look for `frontpage.pdf` in the `pdf/` directory.

* **`python create.py material`**<br />
Creates PDFs of all songs and sketches. Look for them in the `sange/` and `sketches/` directories.

* **`python create.py individual`**<br/>
Creates PDFs for each actor containing only the sketches and songs the actor participates in. Look for the file in the `pdf/individuals` directory.

* **`python create.py signup`**<br/>
Create a sign-up form for all sketches and songs. Look for `rolletilmelding.pdf` in the `pdf/` directory.

> Herfra kommer der et skift i stil, hvilket den opmærksomme læser (eller læseren, som kan bruge `git blame`) måske kan gætte følger med et skift i forfatter.

* **`python create.py --tex-all`**  
Gennemtving gen-TeXning af alle filer. Kan også kobles på de andre kommandoer, for at tvinge gen-TeXning af udvalgte filer.
> Det var, og er, en valgmulighed i `revytex.conf`-filen, men det er en god mulighed at have på kommandolinjen også.

#### Omfattende omskrivninger
Farlige kommandoer, som skriver om i kilde-TeX-filerne. Men dog så usikre på sig selv, at de be'r om bekræfigelse før de gør noget.

* **`python create.py uniform-revue` og `python create.py uniform-year`**  
Revyster husker ikke altid, at skrive det rigtige år, eller den rigtige revy, i deres TeX-filer. De her kommandoer opdaterer alle TeX-filerne i `.plan`-en med revynavn hhv. -år fra `revytex.conf`-filen.

* **`python create.py role-distribution`**  
Skriv roller ind i alle TeX-filer, når rollefordelingen er på plads. Læg filen `roller.csv` i din revy-mappe (eller skriv din fil ind under "Files" som "roller = [filnavn]" i `revytex.conf`). Der er et eksempel i git-mappen, men formatet er basalt set det samme som rollefordelingsskemaet, men i csv-format.

### Om `.csv`-filer
`.csv`-filer kan også bruge semikolonner til at separere værdier, hvilket især er brugbart, når kommaer kan optræde i andre kontekster. Ikke desto mindre laver bl.a. Google Sheets `.csv`-filer med kommaer, så vi prøver at være smarte omkring det. Vi går ud fra, at det tegn af de to (`;` eller `,`), som optræder oftest i csv-filen, er separatortegnet. Det er muligt, at dette kan give anledning til fejl...
