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

> ...for kernefunktionerne

* [Python][python] 3.12 or newer.
* [PyPDF][] for the PDF magic.
* [ordered_set][] for an ordered set.

When dependencies are met, just put the contents of FysikRevyTeX in a directory of your choice. No installation is required.

FysikRevyTeX has been tested on Linux with Python 3.3 and PyPDF2 v. 1.20.

> Opdateret og testet på Windows med Python 3.12 og PyPDF v. 4.2.0

> En del af FysikRevyTeX's ekstra funktioner har knopskudt ekstra afhængigheder, som der nu er indført `requirements.txt`–filer til at holde styr på. Hvis du kun vil installere det absolut nødvendige kan du give kommandoen

    $ pip install -r requirements.txt

> i FysikRevyTeX's rodbibliotek. Hvis du vil installere afhængighederne til alle funktionerne, så er kommandoen

    $ pip install -r all-requirements.txt

> Afhængigherne til de individuelle funktioner bliver beskrevet, når det bliver relevant herunder.

[python]: https://www.python.org/downloads/
[pypdf]: https://pypdf.readthedocs.io/en/stable/index.html
[ordered_set]: https://pypi.org/project/ordered-set/

## Usage
### Creating a new revue directory
The FysikRevyTex directory itself is not meant to be touched at any time (except for development). Instead, you need to set up a new directory for your revue:

    $ cd FysikRevyTeX/
    $ python setup.py path/to/directory

where `path/to/directory` should be where you want to set up the revue directory, e.g. `../2014`. 

> Windows er blevet mere striks omkring oprettelse af symlinks. Derfor har setup-programmet brug for administratorrettigheder, for at kunne oprette revy-mappen. (Dvs. den skal køres fra en terminal, som er startet ved at højreklikke på genvejen og vælge 'Kør som administrator'.)

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
    # langt sceneskift...
    sange/kondoeffekt.tex

    Akt 2
    sange/kvanter_i_maaneskin.tex
    sketches/find_holger.tex

    Akt 3
    sange/konstantens_klagesang.tex

    Ekstranumre
    sange/oppenheimerstyle.tex

> Linjer, som starter med `#` bliver ignoreret som kommentarer (virker med registerindekset siden [ucph-revy][] version 1.2.0).

> Det er også muligt at lave stub-punkter i aktoversigten, som ikke hører til en `.tex`–fil, ved at skrive metadata–tex–kommandoer direkte i `.plan`–filen. De kommer så med i aktoversigten og rollelisten, måske, afhængigt af indstillingerne i `revytex.comf`, og i tidsdiagrammet. Kommandoerne skal stå på en enkelt linje!
>
> Man kunne for eksempel tilføje til *Akt 2* i eksemplet:

    Akt 2
    sange/kvanter_i_maaneskin.tex
    \title{Tag mig med til Brorfelde}\eta{3:48}\melody{Kim Larsen: ``Tag mig med''}\status{Knasende}\revyname{Matematikrevyen}\revyyear{2008}\category{Fisk}
    sketches/find_holger.tex

> Læg mærke til, at `\category` ikke er en af [ucph-revy][]'s kommandoer. Det her script kategoriserer materiale efter navnet på den mappe, de ligger i. Når der ikke er nogen fil, at lægge i en mappe, måtte vi finde på et alternativ.
>
> Husk også, at det ikke er påkrævet, at medtage alle kommandoerne.
>
> Det kræver igen minimum [ucph-revy][] version 1.2.0 for at virke med registerindekset.
>
> En sidebemærkning: [ucph-revy][] er ikke forberedt på, at der kan optræde andre kommandoer, end dem i eksemplet, i planfilen. Det er kun relevant, hvis `thumbindex` er slået til, og [ucph-revy][] kan forberedes på, at der forekommer andre kommandoer, med kommandoen `\planfileAllowMacros`. Det burde i pincippet være muligt, at lægge et rolleafsnit ind i en stub i planfilen, så længe det gøres uden linjeskift. Men det er ikke testet!

#### 3. Edit configuration (optional)
FysikRevyTeX can be configured by editing the file `revytex.conf`. This is also where properties of the front page can be changed.

> Scriptet kan finde på at brokke sig, hvis du har en `revytex.conf`–fil til en gammel version. Der ligger en skabelon, med alle de påkrævede indstillinger, under `templates`.

> I `.conf`-filen kan værdien `version` enten være en kommasepareret liste over versionsnavne, hvoraf den sidste bliver brugt som den nuværende version, eller kun den nuværende version, hvor listen over tidligere versioner så slet ikke bliver sat på forsiden.

#### 4. Rejoice!
You should have a fully working FysikRevyTeX system! See **Day-to-day usage** for instructions on how to use FysikRevyTeX.

> Hvis du har brug for hjælp til at huske alle kommandoerne, så prøv  

    $ python create.py --help
> eller

    $ python create.py -h

>#### 5. Installer PdfSizeOpt (valgfri)
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

> * **`python cretate.py `_‹planfil›_**  
> Det er muligt, at angive en anden planfil end `aktoversigt.plan` som et af argumenterne. Det skal være en fil, som allerede eksisterer.

* **`python create.py aktoversigt`**<br />
Creates the act outline (a "table of contents") for the revue. Look for `aktoversigt.pdf` in the `pdf/` directory.

> Der er indstillinger i `revytex.conf` til hvorvidt stubbe i planfilen skal medtages, og for hvilke kategorier, numre skal oplistes med nummer i stedet for navnet på deres kategori.

> * **`python create.py thumbindex`**<br />
> Bygger indekssiden til registermærkningerne. Husk, at hvis manuskripsider skal have registermærkninger, så skal dokumentklassen kaldes med argumenterne `thumbindex` og `planfile=`_[stil til planfilen]_. Fx:

    \documentclass[thumbindex,planfile=../aktoversigt.plan]{ucph-revy}
    
> Indekssiden bliver automatisk sat, når `create.py` bliver kaldt uden kommandoer, eller med `manus`. Det kan slås fra i `revytex.conf`.

* **`python create.py roles`**<br />
Creates the role/sketch matrix. Look for `rolleliste.pdf` in the `pdf/` directory.
> Rollelisten bruger den korte titel, hvis angivet for et nummer, som er tilgængelig fra [ucph-revy][] version 1.2.0 og frem.

> Instruktører (oplistet i `instructors`-miljøet) markeres med det første bogstav i deres instruktørrolle (eller _i_) som minuskel og kursiv, hvis de ikke har andre roller.

> Der findes indstillinger i `revytex.conf` til at fjerne numre, som ikke har nogen roller defineret, eller filtrere på kategorier.

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

* **`python create.py timesheet`**  
TeX et diagram, der viser hvornår revy(s/t)er er på og af scenen, og i hvor lang tid. Det er beregnet til at være en hjælp til at lægge ninjaplan ud fra.

    **En finte omkring instruktører:** Instruktører, koreografer o.lign. er i udgangspunktet ikke på scenen, selvom deres nummer er på. Så de burde ikke markeres i diagrammet, som om de er på scenen. En løsning er, at flytte dem til `instructors`-miljøet (det har været der hele tiden, kig i manualen til [ucph-revy][]). Det er (nu) også muligt at sætte folk i instruktørroller via den automatiske rollefordeling, som er beskrevet længere nede.

* **`python create.py roles-sheet`**  
Lav en `.csv` (bedst til Excel) eller `.tsv` (til Google Sheets) –fil med en oversigt over rollerne i manuskriptets TeX-filer, som inkluderer en ordtælling for hver rolle. Ændringer i den her fil kan tilbageføres til TeX-filerne med kommandoen `role-distribution` længere nede.

    Der er også en ordtælling af replikker og sangtekster for hver rolle, som måske kan bruges som input i rollefordelingen. Og hvis rollefordelingen kan slutte med en fil i det her format, så har den TeX-ansvarlige sparet en opgave ;)

    Filnavnet sættes enten i `conf`–filen, eller med valgmuligheden `--roles-sheet-fn=<filnavn>`.

#### Funktioner, der interagerer med Google dokumenttyper ####

For at bruge de her funktioner, skal python kunne kontakte din google-konto. For at sætte din google-konto op, skal du følge trinnene i [gspread][]s dokumentation (hvis du er i tvivl, brug trinene "For End Users". Men trinene "For Bots" virker også), eller [dokumentationen for Googles Forms–API][gforms-authorize].

* **`python create.py props`**<br />
Eksporterer de rekvisitter, som er skrevet ind i `props`--miljøet i `.tex`--filerne, til et regeark på Google Sheets. Integrationen kræver [gspread][]. Den relevante `requirements`–fil hedder `sheets-requirements.txt`.

    For at sætte op, følg de her trin:

    1. Sæt din google–konto op som beskrevet i starten af det her afsnit.
    2. Find eller lav et tomt ark i et regneark, som du har redigeringsrettigheder til i Google Sheets. Hvis arket ikke er tomt (helt præcist, hvis celle `A1` ikke er tom), bliver overskrifterne ikke autogenereret.
    3. Skriv regnearkets og arkets navne ind i din `revytex.conf`, og sæt `skip gspread` til `no`.
    4. Kør `python create.py props`, og se regnearket blive fyldt op (hvis dine revyster rent faktisk har skrevet deres rekvisitter ind...)
    
* **`python create.py google-forms-signup`**  
Sætter akter, titler og roller ind i en kopi af en Google Form, som er forberedt med pladsholdere til dem. Kan også sætte revydatoer ind, til til- eller afmelding, hvis den får en kalenderfil i iCalendar–format (i Google Calendar ligger der et link til sådan en fil i settings–siden for den enkelte kalender. Scriptet kan hente kalender–flier fra internettet, hvis det får en url). [Her er et eksempel på, hvordan pladsholderne kan sættes ind i en Form][forms-ex].

    For at bruge, gør først din Google–konto klar, som beskrevet først i det her afsnit. Efter det spørger den her kommando selv efter de informationer, som den skal bruge, hvis de ikke er skrevet ind i `revytex.conf`. Hvis du vil skrive kommandoerne ind i `revytex.conf`, så får du til sidst en tekstblok, som kan klippe–klistres ind (men hvorfor skulle du egentlig ville det...?)
    
    Hvis du ikke er tilfreds med rollerne, som de står skrevet i TeX–filerne, så er `roles-sheet` og `role-distribution` effektive redskaber til hurtigt at lave dem om.
    
    Den her kommando har afhængigheder (jf. [API–dokumentationen][gforms-deps]) til en del google-pakker, og også til `oauth2client`, som [nok burde erstattes][oauthissue]. Sammenfattet i `forms-requirements.txt`
    
    Hvis du vil læse kalenderfiler, så skal vi også bruge et [iCalendar–bibliotek][ical] og et [tidszonebibliotek][pytz], som er opremset i `cal-requirements.txt`.

[gspread]: https://docs.gspread.org/en/latest/index.html

[gforms-authorize]: https://developers.google.com/forms/api/quickstart/python#set_up_your_environment

[forms-ex]: https://docs.google.com/forms/d/e/1FAIpQLSdDtqx_FdYhHTWVWstKFnMmUTI_Rc5hyOTOw6FPxRTupvXW5Q/viewform?usp=sf_link

[gforms-deps]: https://developers.google.com/forms/api/quickstart/python#install_the_google_client_library

[ical]: https://pypi.org/project/ical/

[pytz]: https://pypi.org/project/pytz/

[oauthissue]: https://github.com/FysikRevy/FysikRevyTeX/issues/17


#### Flag og valgmuligheder ####

* **`python create.py --tex-all`**  
Gennemtving gen-TeXning af alle filer. Kan også kobles på de andre kommandoer, for at tvinge gen-TeXning af udvalgte filer.

* **`python create.py -v`**  
Skriv output fra LaTeX til terminalen (v for "verbose"). Scriptet paralleliserer TeXningen, så du får nok en overvældende mængde output fra kommandoer, som TeXer flere ting.

> `--tex-all` og `-v` var, og er, en valgmulighed i `revytex.conf`-filen, men de er en gode muligheder at have på kommandolinjen også.

* **`python create.py --single-thread` (eller `-s`)**  
Slå parallelkørsel af TeX-ning og pdf-sammensætning fra. Hvis det giver problemer.

* **`python create.py --max-parallel=`〈_antal_〉**  
Sæt antallet af processer, som python må starte til at køre opgaver parallelt, hvis du tror, du ved bedre end standarderne. (Der kan måske være fornuft i at sætte tallet højere end standarden, som er antallet af os-kerner, siden vores opgaver skal læse og skrive en del. Alt afhængigt af forholdet mellem hastigheden af din disk og cpu. Her er plads til eksperimentering, hvis du tror, du ved bedre end standarderne.) Det samme som `-s`, hvis sat til 1.

#### Omfattende omskrivninger
Farlige kommandoer, som skriver om i kilde-TeX-filerne. Men dog så usikre på sig selv, at de be'r om bekræfigelse før de gør noget.

* **`python create.py uniform-revue` og `python create.py uniform-year`**  
Revyster husker ikke altid, at skrive det rigtige år, eller den rigtige revy, i deres TeX-filer. De her kommandoer opdaterer alle TeX-filerne i `.plan`-en med revynavn hhv. -år fra `revytex.conf`-filen.

* **`python create.py role-distribution`**  
Skriv roller ind i alle TeX-filer. Rollefordelingsfiler kan have flere forskellige formater, men skal enten være en `.csv`, `.ssv` eller `.csv`-fil. Når du har en rollefordeligsfil, kan den enten skrives ind i `revytex.conf`, eller gives til kommandolinjen som `--<formatnavn>=<filnavn>`, altså `--pdf-matrix=roller.csv`, hvis du vil bruge eksempelfilen.

    Formaterne er:
    
    * **`pdf-matrix`**: basically det samme format som rollefordeligsoversigten, som bliver typesat i manuskriptet, men som en `.csv`–fil. Eksempelfilen `roller.csv` er inkluderet her i repo'et.
    
        De første par linjer i eksempelfilen udpeger hvilke forkortelser svarer til instruktørroller. De kan udelades, hvis det ikke er relevant (i så fald vil rollefordelingsprocessen ikke røre ved `instructors`-miljøet i .tex-filerne, hvis de indeholder et). Hvis de er med, _skal_ de forekomme før navnelinjen (vi går ud fra, at navnelinjen er den første linje, der starter med et tomt felt), de skal have formatet 〈_fork._〉` = `〈_instruktørrolle_〉. Hver forekomst skal stå i det første felt i sin række (eller skal være efterfulgt af mindst ét separatortegn, hvis du skriver rå tekst).
        
        Det er ikke muligt, at tildele samme revy(s)t flere roller i samme nummer i det her format.
    * **`overview`**: formatet, som bliver udlæst af kommandoen `roles-sheet`. Dog er overskrift-kolonnen valgfri. Rækkerne med ordantal bliver ignoreret, og behøver ikke at være der. Kolonnen med aktnavne ignoreres, og behøver ikke at udfyldes. For hvert nummer kan filnavn eller titel udelades. Hvis begge er angivet prioriteres filnavnet.
    
        Rækken, der hedder `"Instruktørroller"` kan udelades. For hvert nummer, hvor der ikke findes sådan en række, bliver `instructors`-miljøet ikke ændret, hvis det findes i den tilsvarende .tex-fil. Hvis en revy(s)t er blevet tildelt en forkortelse og en instruktørrolle, bliver forkortelsen ignoreret, og dén revyst vil kun få instruktørrollen skrevet ind. Hvis en revy(s)t er blevet tildelt både en instruktørrolle og en rollebeskrivelse, bliver begge skrevet ind i .tex-filen.
    
    Den her funktion afhænger af [thefuzz][] til at forbinde titler, som ikke er helt ens. Den afhængighed er også skrevet ind i `dist-requirements.txt`.

* **`python create.py enforce-twoside`**  
Giv valgmuligheden `twoside` til `\documentclass` i alle `.tex`-filer. Bør bruges sammen med valgmuligheden i `revytex.conf`, som indsætter blanke bagsider, men den er sat til som standard. Den her indstilling er god i samspil med registermærkerne, se `enable-thumbtabs` længere nede.

* **`python create.py enforce-class`**  
Sætter `\documentclass{ucph-revy}` i alle `.tex`-filer. Fjerner samtidig `\usepackage{revy}`. `ucph-revy` burde være tilægnelig i en opdateret LaTeX-distribution. Ellers er den på [CTAN][ucph-revy].

* **`python create.py enable-thumbtabs`**  
Sætter indstillingerne, som får registermærkerne sat i de individuelle materialefiler. Det indebærer, at give valgmulighederne `thumbindex` og `planfile=../aktoversigt.plan` (eller hvad den rigtige relative sti nu er) til dokumentklassen i hver `.tex`-fil. Det gør kun noget, hvis dokumentklassen er `ucph-revy`, se `enforce-class` herover.

  Hvis du ikke bruger registermærker, og gerne vil undgå siden med registerindekset, så er der en indstilling til at slå den fra i `revytex.conf`-filen. Det er så stadig muligt, at få indekssiden med i en given kørsel, hvis du også giver kommandoen `thumbindex`. Altså for eksempel `python create.py thumbindex manus`. Hvorvidt der bliver sat registermærker på i de enkelte materialefiler afhænger stadig udelukkende af, om `thumbindex` er sat i `.tex`-filen.

* **`python create.py overleaf-compat`**  
Den her er nok ikke nødvendig længere, iflg. #25

  [Overleaf][] har haft en nøkke med, at filer altid bliver kompileret fra rodmappen. Det passer ikke med den måde, `ucph-revy` leder efter `aktoversigt.plan`. Den her kommando flytter rundt på, hvordan filerne er organiseret omkring planfilen, så materiale kan kompileres med registermærkninger både lokalt og på Overleaf. Men læg mærke til, at det kun er registermærkerne, der bliver påvirket af det her.

  Det foregår ved, at fjerne `planfile`-argumentet fra `.tex`-filerne igen, så de altid går ud fra, at planfilen hedder `aktoversigt.plan`, og ligger i samme mappe. Derefter laver vi en kopi af `aktoversigt.plan` i alle mapperne, hvor der er `.tex`-filer, som er nævnt i `aktoversigt.plan`, hvor stierne er ændret, så de er rigtige set inde fra undermapperne. Det betyder så, at hvis der bliver lavet om på `aktoversigt.plan`, så skal den her kommando køres igen, for at opdatere kopierne. Læg mærke til, at det er når manuskriptet TeX-es lokalt, at det er nødvendigt, at kopierne er opdateret.

[Overleaf]: https://overleaf.com

[thefuzz]: https://pypi.org/project/thefuzz/


### Om `.csv`-filer
`.csv`-filer kan også bruge semikolonner til at separere værdier, hvilket især er brugbart, når kommaer kan optræde i andre kontekster. Ikke desto mindre laver bl.a. Google Sheets `.csv`-filer med kommaer, så vi prøver at være smarte omkring det. Vi godtager også `.tsv`--filer, hvor seperatoren er et tabulatortegn (pas på med at vise dem til almindeligt revyster, som måske ikke kan se forskel på tabulatortegn og mellemrum). Vi går ud fra, at det tegn af de tre mulige (`tab`, `;` eller `,`), som optræder oftest i (c/t)sv-filen, er separatortegnet. Det er muligt, at dette kan give anledning til fejl...
