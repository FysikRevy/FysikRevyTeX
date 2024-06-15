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

> Opdateret og testet på Windows med Python 3.11 og PyPDF2 v. 3.0.1

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

> ##### Om `ucph-revy.cls` og `revy.sty`
> [Ret beset][Overleaf-class] burde revyens LaTeX-pakke vel altid have været en dokumentklasse. Så det er den nu. Den hedder `ucph-revy`, og den ligger på [CTAN][ucph-revy]. Den burde være til at finde for MikTeX og TeXLive, og måske dukker den også op i Overleaf en dag...
>
> Den eneste rigtig store tilføjelse til `ucph-revy` over `revy.sty` er LaTeX-koden til at lave registermærkninger på manuskriptsider, det er de grå og sorte kasser i kanten af siderne på billedet. I bund og grund udnytter TeX de samme filer som FysikRevyTeX, til at lave dem. Der er nogle kommandoer, der får det hele til at virke, længere nede på siden.

[Overleaf-class]: https://www.overleaf.com/learn/latex/Understanding_packages_and_class_files
[ucph-revy]: https://ctan.org/pkg/ucph-revy

![Eksempel på manuskriptsider sat med ucph-revy.cls](https://raw.githubusercontent.com/FysikRevy/FysikRevyTeX/master/eksempel.png)

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

> Hvis du har brug for hjælp til at huske alle kommandoerne, så prøv  

    $ python create.py --help
> eller

    $ python create.py -h

>#### 5. Installer PdfSizeOpt
> [PdfSizeOpt][] er et (python 2) program, som kan optimere størrelsen på en PDF--fil. En manuskript--fil, som er limet sammen af mange, mindre, PDF--filer kan ofte reduceres i størrelse med en faktor 10.
>
> For gøre det, start med at installere PdfSizeOpt, som instueret på deres GitHub--side. Læg så den fulde sti til PdfSizeOpts eksekverbare fil (`.exe`--filen under Windows) i en miljøvariabel i `create.py`s miljø, som hedder `PDFSIZEOPT`.
>
> Altså, under *nix, sådan noget som  
> `$ export PDFSIZEOPT=/sti/til/exec`
>
> Under Windows, skriv 'miljø' i startmenuen, og klik ind i den dialogboks, som hedder "Rediger systemmiljøvarablene".

[PdfSizeOpt]: https://github.com/pts/pdfsizeopt


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
> Bygger indekssiden til registermærkningerne. Husk, at hvis manuskripsider skal have registermærkninger, så skal dokumentklassen kaldes med argumenterne `thumbindex` og `planfile=`_[stil til planfilen]_. Fx:

    \documentclass[thumbindex,planfile=../aktoversigt.plan]{ucph-revy}
    
> Indekssiden bliver automatisk sat, når `create.py` bliver kaldt uden kommandoer, eller med `manus`. Det kan slås fra i `revytex.conf`.

* **`python create.py roles`**<br />
Creates the role/sketch matrix. Look for `rolleliste.pdf` in the `pdf/` directory.

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

* **`python create.py roles-sheet`**  
Lav en `.csv` (bedst til Excel) eller `.tsv` (til Google Sheets) –fil med en oversigt over rollerne i manuskriptets TeX-filer, som inkluderer en ordtælling for hver rolle. Ændringer i den her fil kan tilbageføres til TeX-filerne med kommandoen `role-distribution` længere nede.

    Filnavnet sættes enten i `conf`–filen, eller med valgmuligheden `--roles-sheet-fn=<filnavn>`.

* **`python create.py props`**<br />
Eksporterer de rekvisitter, som er skrevet ind i `props`--miljøet i `.tex`--filerne, til et regeark på Google Sheets. Integrationen kræver [gspread][].

    For at sætte op, følg de her trin:

    1. Start med at have en Google--konto. 
    2. Følg skridtene til "Authentication" i [gspread][]s dokumentation. (Hvis du er i tvivl, brug trinene "For End Users". Men trinene "For Bots" virker også.)
    3. Find eller lav et tomt ark i et regneark, som du har redigeringsrettigheder til i Google Sheets. Hvis arket ikke er tomt (helt præcist, hvis celle `A1` ikke er tom), bliver overskrifterne ikke autogenereret.
    4. Skriv regnearkets og arkets navne ind i din `revytex.conf`, og sæt `skip gspread` til `no`.
    5. Kør `python create.py props`, og se regnearket blive fyldt op (hvis dine revyster rent faktisk har skrevet deres rekvisitter ind...)

* **`python create.py --tex-all`**  
Gennemtving gen-TeXning af alle filer. Kan også kobles på de andre kommandoer, for at tvinge gen-TeXning af udvalgte filer.

* **`python create.py -v`**  
Skriv output fra LaTeX til terminalen (v for "verbose"). Scriptet paralleliserer TeXningen, så du får nok en overvældende mængde output fra kommandoer, som TeXer flere ting. Men der er nok den eneste måde at få diagnostisk information fra kommandoer som `aktoversigt` eller `contacts`.

[gspread]: https://docs.gspread.org/en/latest/index.html

> De her var, og er, en valgmulighed i `revytex.conf`-filen, men de er en gode muligheder at have på kommandolinjen også.

#### Omfattende omskrivninger
Farlige kommandoer, som skriver om i kilde-TeX-filerne. Men dog så usikre på sig selv, at de be'r om bekræfigelse før de gør noget.

* **`python create.py uniform-revue` og `python create.py uniform-year`**  
Revyster husker ikke altid, at skrive det rigtige år, eller den rigtige revy, i deres TeX-filer. De her kommandoer opdaterer alle TeX-filerne i `.plan`-en med revynavn hhv. -år fra `revytex.conf`-filen.

* **`python create.py role-distribution`**  
Skriv roller ind i alle TeX-filer, når rollefordelingen er på plads. Læg filen `roller.csv` i din revy-mappe (eller skriv din fil ind under "Files" som "roller = [filnavn]" i `revytex.conf`). Der er et eksempel i git-mappen, men formatet er basalt set det samme som rollefordelingsskemaet, men i csv-format.

* **`python create.py enforce-twoside`**  
Giv valgmuligheden `twoside` til `\documentclass` i alle `.tex`-filer. Bør bruges sammen med valgmuligheden i `revytex.conf`, som indsætter blanke bagsider, men den er sat til som standard. Den her indstilling er god i samspil med registermærkerne, se `enable-thumbtabs` længere nede.

* **`python create.py enforce-class`**  
Sætter `\documentclass{ucph-revy}` i alle `.tex`-filer. Fjerner samtidig `\usepackage{revy}`. `ucph-revy` burde være tilægnelig i en opdateret LaTeX-distribution. Ellers er den på [CTAN][ucph-revy], og der er også inkluderet en kopi af `.cls`-filen i `templates`-mappen.

* **`python create.py enable-thumbtabs`**  
Sætter indstillingerne, som får registermærkerne sat i de individuelle materialefiler. Det indebærer, at give valgmulighederne `thumbindex` og `planfile=../aktoversigt.plan` (eller hvad den rigtige relative sti nu er) til dokumentklassen i hver `.tex`-fil. Det gør kun noget, hvis dokumentklassen er `ucph-revy`, se `enforce-class` herover.

  Hvis du ikke bruger registermærker, og gerne vil undgå siden med registerindekset, så er der en indstilling til at slå den fra i `revytex.conf`-filen. Det er så stadig muligt, at få indekssiden med i en given kørsel, hvis du også giver kommandoen `thumbindex`. Altså for eksempel `python create.py thumbindex manus`. Hvorvidt der bliver sat registermærker på i de enkelte materialefiler afhænger stadig udelukkende af, om `thumbindex` er sat i `.tex`-filen.

* **`python create.py overleaf-compat`**  
[Overleaf][] har en nøkke med, at filer altid bliver kompileret fra rodmappen. Det passer ikke med den måde, `ucph-revy` leder efter `aktoversigt.plan`. Den her kommando flytter rundt på, hvordan filerne er organiseret omkring planfilen, så materiale kan kompileres med registermærkninger både lokalt og på Overleaf. Men læg mærke til, at det kun er registermærkerne, der bliver påvirket af det her.

  Det foregår ved, at fjerne `planfile`-argumentet fra `.tex`-filerne igen, så de altid går ud fra, at planfilen hedder `aktoversigt.plan`, og ligger i samme mappe. Derefter laver vi en kopi af `aktoversigt.plan` i alle mapperne, hvor der er `.tex`-filer, som er nævnt i `aktoversigt.plan`, hvor stierne er ændret, så de er rigtige set inde fra undermapperne. Det betyder så, at hvis der bliver lavet om på `aktoversigt.plan`, så skal den her kommando køres igen, for at opdatere kopierne. Læg mærke til, at det er når manuskriptet TeX-es lokalt, at det er nødvendigt, at kopierne er opdateret.

[Overleaf]: https://overleaf.com

### Om `.csv`-filer
`.csv`-filer kan også bruge semikolonner til at separere værdier, hvilket især er brugbart, når kommaer kan optræde i andre kontekster. Ikke desto mindre laver bl.a. Google Sheets `.csv`-filer med kommaer, så vi prøver at være smarte omkring det. Vi godtager også `.tsv`--filer, hvor seperatoren er et tabulatortegn (pas på med at vise dem til almindeligt revyster, som måske ikke kan se forskel på tabulatortegn og mellemrum). Vi går ud fra, at det tegn af de tre mulige (`tab`, `;` eller `,`), som optræder oftest i (c/t)sv-filen, er separatortegnet. Det er muligt, at dette kan give anledning til fejl...
