from base_classes import Role
from tex import TeX
from fuzzywuzzy import fuzz
from helpers import split_outside_quotes,rows_from_csv_etc

stoptext = """
        ╔═╗╔╦╗╔═╗╔═╗        
======  ╚═╗ ║ ║ ║╠═╝  ======
        ╚═╝ ╩ ╚═╝╩          
Følgende kommando(er):
{}
omskriver dine tex-filer med autogenereret indhold. Det kan gå rigtig
galt, så fortsæt kun, hvis du har en måde, du kan rulle de
omskrivninger tilbage på. Tag en kopi, lav en bakcup, git commit, check
om Time Machine har kigget på den her mappe, eller gør noget andet
endnu smartere.
{}Vil du tage risikoen, og fortsætte nu? (Den her advarsel kan
undertrykkes ved at sige '-y' til scriptet)
(y/[n]):"""

class ClobberInstructions:
    # skelet til rutiner, som skriver tex-filer om:
    @staticmethod
    def init( revue ):
        # analyser, hvilke ændringer vi vil lave. Byg
        # opsummeringer, som en bruger kan tage stilling til, for
        # eksempel. Den her funktion kører en gang, med
        # "revue"-objektet som input

        # Men pas på! Det er muligt, at andre
        # tex-omskrivningsrutiner arbejder på din tex-fil, før din
        # clobber-rutine når til den, så lav ikke for specifik
        # setup her.

        # Din clobber-rutine får outputtet her som input
        return revue
        
    warn = ""
    # skriv dit eget afsnit i advarselsteksten.
    
    @staticmethod
    def clobber( tex, initresult ):
        # det er her, vi laver ændringer i individuelle
        # tex-filer. Bliver kaldt en gang for hvert
        # "Material"-objekt i "revue", med et "TeX"-objekt, som
        # har parset den relevante tex-fil, og resultatet af
        # "init"
        return tex

class RoleDistribution( ClobberInstructions ):
    # automatisk rollefordeling.
    @staticmethod
    def init( revue ):

        if "role_names" in revue.conf["Files"] \
           and revue.conf["Files"]["role_names"]:
            try:
                rolenamerows = rows_from_csv_etc(
                    revue.conf["Files"]["role_names"]
                    )
                print("Bruger {} som rollenavneliste.\n".format(
                    revue.conf["Files"]["role_names"]
                    ))
            except FileNotFoundError:
                print(
                    "Kunne ikke finde filen {}, "
                    + "som er angivet i conf-filen.\n"
                    .format( revue.conf["Files"]["role_names"] )
                    )
            else:
                rolenamedict = {}
                for row in rolenamerows[1:]:
                    rolenames = {}
                    for abbr, name in zip( rolenamerows[0][1:], row[1:] ):
                        if name:
                            rolenames[ abbr ] = name
                    rolenamedict[ row[0] ] = rolenames
                
        fname = ( revue.conf["Files"]["roller"]
                  if "roller" in revue.conf["Files"]
                  else "roller.csv"
        )

        try:
            role_rows = rows_from_csv_etc( fname )
            print("Bruger {} til rollefordeling.\n".format( fname ) )
                
        except FileNotFoundError:
            print("""
Kunne ikke finde csv-filen til rollefordeling:
({})
Så det springer vi over denne gang.
""".format( fname )
            )
            clobber_steps[ "role-distribution" ] = ClobberInstructions

        else:
            # prøv at gætte sammenhængen mellem nummer-navne i
            # rollefordelingsfilen og manuskriptfilerne, med fuzzy
            # matching, se https://pypi.org/project/fuzzywuzzy/
            materials = [ material for act in revue.acts
                          for material in act.materials ]

            def rolename_when_exists( title, abbr ):
                try:
                    return rolenamedict[ title ][ abbr ]
                except:
                    return ""
            
            scorechart = {
                row[0]: {
                    "scores": [ fuzz.partial_ratio( material.title, row[0] )
                                for material in materials ],
                    "roles": [ Role( abbr, name, rolename_when_exists( row[0], abbr ) )
                               for abbr, name in zip(
                                       row[1:], role_rows[0][1:]
                               ) if abbr
                    ]
                }
                for row in role_rows[1:]
            }
            translations = {}

            while scorechart:
                # tag gættet med den højeste sikkerhed hver gang,
                # og fjern den tilhørende række og kolonne fra
                # tabellen
                best = max( scorechart,
                            key=lambda key: max(
                                scorechart[ key ][ "scores" ]
                            ))
                maxindex = scorechart[ best ][ "scores"
                ].index( max( scorechart[ best ][ "scores" ]))
                translations[ best ] = {
                    "material": materials[ maxindex ],
                    "conf": scorechart[ best ][ "scores" ][ maxindex ],
                    "roles": scorechart[ best ][ "roles" ]
                }
                for name in scorechart:
                    scorechart[ name ][ "scores" ][ maxindex ] = 0
                del scorechart[ best ]
                # TODO: find på bedre navne end 'best' og 'maxindex'

            # lad den TeX-ansvarlige tage stilling til, hvad der
            # kommer til at ske
            print("""
Navn i fordelingsfil:              => Skh.: Titel på gæt:
--------------------                  ----  ------------""")
            for t in translations:
                print("{:<35}=> ({:>3}) {:<36}".format(
                    t[:35],
                    translations[t]["conf"],
                    translations[t]["material"].title[:36]
                ))
            
            return { translations[t]["material"].title:
                     translations[t][ "roles" ]
                     for t in translations }

    warn = """
Vi prøver at gætte på hvilket nummer hver linje i rolle-filen
refererer til, ved at sammenligne navnet med titlerne på de numre, vi
kender. Du kan se vores gæt ovenfor, sammen med et tal for hvor sikre
vi er. Hvis vores gæt ikke er rigtige, er det nu, du skal springe fra.
"""
    
    @staticmethod
    def clobber( tex, translations ):
        if tex.info[ "title" ] in translations:
            # beklager, Mario. Din fuktion bor i en anden fil
            tex.update_roles(
                translations[ tex.info[ "title" ]]
            )
        return tex

def valueReplace( texname, confname ):
    # giv mig en fuktion, som sætter en værdi fra conf-filen ind i
    # en tex-kommando
    def vr( tex, revue ):
        newline = "\\" + texname + "{" \
                  + revue.conf[ "Revue info" ][ confname ] + "}\n"
        for ln, line in enumerate( tex.info[ 'tex' ]):
            if "\\" + texname in line:
                tex.info[ 'tex' ][ ln ] = newline
                break
        else:
            # Hvis der ikke er en kommand at erstatte, sæt kommandoen
            # ind lige for \begin{document}
            def insert():
                for line in tex.info[ 'tex' ]:
                    if "\\begin{document}" in line:
                        for x in [ newline, line ]:
                            yield x
                    else:
                        yield line

            tex.info[ 'tex' ] = list( insert() )
        return tex

    return vr

# for de to her overskriver vi kun clobber-trinnet
class UniformRevue( ClobberInstructions ):
    clobber = valueReplace( "revyname", "revue name" )

class UniformYear( ClobberInstructions ):
    clobber = valueReplace( "revyyear", "revue year" )

clobber_steps = {
    "role-distribution" : RoleDistribution,
    "uniform-revue"     : UniformRevue,
    "uniform-year"      : UniformYear
}

def clobber_my_tex( revue, args ):
    "Methods that rewrite your tex files."
    
    initresults = { cmd: clobber_steps[ cmd ].init( revue )
                    for cmd in clobber_steps if cmd in args
    }
    cont = input(
        stoptext.format(
            "\n".join( "  " + arg for arg in clobber_steps if arg in args ),
            "\n".join([
                clobber_steps[ arg ].warn for arg in clobber_steps if (
                    arg in args
                    # ingen linjeskift for tomme strenge
                    and clobber_steps[ arg ].warn 
            )
        ]) + "\n" )
    ) if not '-y' in args else 'y' # spring advarsel over
    
    if cont == 'y':
        tex = TeX( revue )
        for material in [ material for act in revue.acts
                          for material in act.materials ]:
            fname = material.path
            tex.parse( fname )
            for cmd in clobber_steps:
                if cmd in args:
                    tex = clobber_steps[ cmd ].clobber(
                        tex, initresults[ cmd ]
                    )
            tex.write( fname )
            material.modification_time = tex.info[ "modification_time" ]
