import re
import os
from operator import itemgetter
from pathlib import Path
from base_classes import Role
from tex import TeX
from roles_reader import formats

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

    cmd = "thing-do"
    # argumentet til programmet, som udløser den her handling
    doc = "Does a thing"
    # beskrivelse til "--help" argumentet.
    # prøv at hold under 60 bogstaver
    
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
    cmd = "role-distribution"
    doc = "Skriver rollefordelingen ind i .tex-filerne, hvis angivet i konfigurationen."
    
    @staticmethod
    def init( revue ):

        active_formats = [ form for form in formats
                           if revue.conf.conf.has_option( "Files", form.name )
                          ]

        if len( active_formats ) != 1:
            if len( active_formats ) == 0:
                print( "Ingen rollefordelingsfiler er angivet." )
            else:
                print( "For mange rollefordelingsfiler er angivet:" )
                for form in active_formats:
                    print( "    {} = {}".format(
                        form.mane, revue.conf.conf.get( "Files", form.name )
                    ))

            clobber_steps[ "role-distribution" ] = ClobberInstructions
            print( "Så rollefordelingen bliver sprunget over denne gang." )
            return

        active_format = active_formats[0]
        materials = [ material for act in revue.acts \
                      for material in act.materials ]
        try:
            translations, scorechart = \
                itemgetter("translations","scorechart")(
                    active_format.reader(
                        revue.conf.conf.get(
                            "Files", active_format.name,
                            fallback = active_format.default_filename ),
                        revue
                    )
                )
        except FileNotFoundError:
            print("Kunne ikke læse filen til rollefordeling: {}".format(
                revue.conf.conf.get( "Files", active_format.name,
                                     fallback = active_format.default_filename )
            ))
            clobber_steps[ "role-distribution" ] = ClobberInstructions
            print("Så rollefordelingen bliver sprunget over denne gang.")
            return

        print("Rollefordelingsfilen er {}, som burde have formatet '{}'"\
              .format(
                  revue.conf.conf.get(
                      "Files", active_format.name,
                      fallback = active_format.default_filename
                  ),
                  active_format.name
              )
              )

        if len( translations ) > 0:
            print("""
Følgende materialer er nævnt ved filnavn i rollefordelingsfilen:

Filnavn:                                Titel:
--------                                ------""")
            for t in translations:
                print( "{:<39} {:<39}".format(
                    Path( translations[t]["material"].path )\
                        .relative_to( Path.cwd() )\
                        .as_posix()[:39],
                    translations[t]["material"].title[:40]
                ) )

        if len( scorechart ) > 0:
            print("""
Følgende materialer er matchet efter titel:

Navn i fordelingsfil:              => Skh.: Titel på gæt:
--------------------                  ----  ------------""")

        while scorechart:
            # tag gættet med den højeste sikkerhed hver gang,
            # og fjern den tilhørende række og kolonne fra
            # tabellen
            best = max( scorechart,
                        key=lambda key: max(
                            scorechart[ key ][ "scores" ]
                        ))
            maxindex = scorechart[ best ][ "scores" ]\
                .index( max( scorechart[ best ][ "scores" ]))
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
        for t in translations:
            if translations[t]["conf"] != "fn":
                print("{:<35}=> ({:>3}) {:<36}".format(
                    t[:35],
                    translations[t]["conf"],
                    translations[t]["material"].title[:36]
                ))
            
        return { translations[t]["material"].title:
                 translations[t][ "roles" ]
                 for t in translations }

    warn = """
Vi prøver at gætte, hvilke numre rollefordelingsfilen refererer til,
hvis den ikke indeholder filnavne, ved at sammenligne navnet med
titlerne på de numre, vi kender. Du kan se vores gæt ovenfor, sammen
med et tal for hvor sikre vi er. Hvis vores gæt ikke er rigtige, er
det nu, du skal springe fra.
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
    cmd = "uniform-revue"
    doc = "Skriv revyens navn (fra revytex.conf) ind i .tex-filerne"
    clobber = valueReplace( "revyname", "revue name" )

class UniformYear( ClobberInstructions ):
    cmd = "uniform-year"
    doc = "Skriv revyåret (fra revyconf.tex) ind i .tex-filerne"
    clobber = valueReplace( "revyyear", "revue year" )

def find_documentclass( tex_info_tex ):
    return next(
        ( (i,line) for i,line in enumerate( tex_info_tex )
          if re.match(r"[^%]*\\documentclass", line) )
    )

def enable_classopts( opts, tex ):
    if not isinstance( opts, list ):
        opts = opts.split( "," ) # and just throw if you can't

    try:
        i,line = find_documentclass( tex.info['tex'] )
    except StopIteration:
        return tex          # større problemer...
    old_opts = re.search( r"\\documentclass([^{]*){", line )
    if not old_opts:
        return tex          # noget skidt TeX...
    if re.fullmatch( r"[][\s]*", old_opts[1] ):
        tex.info['tex'][i] = line[ 0 : old_opts.start(1) ] \
            + "[{}]".format( ",".join( opts ) ) \
            + line[ old_opts.end(1): ]
    else:
        newopts = [ opt for opt in opts if not
                    re.search( "[\\[,]{}[\\],]".format( opt ), old_opts[1] )
                   ]
        if len(newopts) > 0:
            tex.info['tex'][i] = re.sub(
                r"(\\documentclass[^[]*)\[",
                "\\1[{},".format( ",".join( newopts )),
                line,
                count=1
            )
    return tex
    
class EnforceTwoside( ClobberInstructions ):
    cmd = "enforce-twoside"
    doc = "Sæt 'twoside' i alle .tex-filers \\documentclass"

    @staticmethod
    def clobber( tex, revue ):
        return enable_classopts( "twoside", tex )

class EnforceClass( ClobberInstructions ):
    # den her *burde* kun være nødvendig i en overgangsperiode
    cmd = "enforce-class"
    doc = "Gennemtving brug af 'ucph-revy.cls' i stedet for 'revy.sty'."

    def clobber( tex, revue ):
        try:
            classline = find_documentclass( tex.info['tex'] )
        except StopIteration:
            return              # ikke mit problem
        styline = next(( (i,line) for i,line in enumerate( tex.info['tex'] )\
                         if re.match( r"[^%]*\\usepackage[^{]*{revy}",
                                      line
                                     )
                        ), None)
        if styline:
            styopts = re.search( r"\\usepackage\[([^]]*)\]{revy}",
                                 styline[1] )
            if styopts:
                styopts = styopts[1]
        else:
            styopts = None
        clsopts = re.search( r"\\documentclass\[([^]]*)]", classline[1] )
        if clsopts:
            clsopts = clsopts[1]
        newopts = ",".join([opt for opt in [clsopts,styopts]
                            if opt and len(opt) > 0 ])
        tex.info['tex'][classline[0]] = \
            re.sub( r"documentclass[^}]*}",
                    "documentclass{}{}ucph-revy{}".format(
                        "[{}]".format( newopts ) if len(newopts) > 0
                        else "",
                        "{",
                        "}"
                    ),
                    classline[1]
                   )
        if styline:
            newsty = re.sub( r"\\usepackage[^{]*{revy}",
                             "",
                             styline[1]
                            )
            if re.fullmatch( r"\s*", newsty ):
                tex.info['tex'] = tex.info['tex'][:styline[0]] \
                    + tex.info['tex'][styline[0]+1:]
            else:
                tex.info['tex'][styline[0]] = newsty

        return tex

class EnableThumbtabs( ClobberInstructions ):
    cmd = "enable-thumbtabs"
    doc = "Slå TeXning af registermærkninger til i .tex-filerne."
    warn = """
Registermærkningerne kræver, at dine .tex-filer har
  \\documentclass{ucph-revy}
Se også enforce-class.
"""

    def clobber( tex, revue ):
        tex = enable_classopts( "thumbindex", tex )
        planpath = os.path.relpath(
            os.path.abspath( "aktoversigt.plan" ),
            start = os.path.dirname( tex.fullpath )
        ).replace( "\\", "/" )
        try:
            i,line = find_documentclass( tex.info['tex'] )
        except StopIteration:
            return tex
        documentopts = re.search( r"documentclass\[([^]]*)\]", line )
        newopts = re.sub( r",?planfile=[^],]*", "", documentopts[1] )\
            + ",planfile=" + planpath
        tex.info['tex'][i] = line[:documentopts.start(1)] \
            + newopts \
            + line[documentopts.end(1):]
#        tex.info['tex'][i] = line
        return tex

class OverleafCompat( ClobberInstructions ):
    # Overleaf flytter altid den .tex-fil, der bliver kompileret, til
    # rodmappen. Hvis "planfile" i .tex-filerne bare peger på
    # "aktoversigt.plan" i rodmappen, så kan Overleaf ikke finde
    # den. I stedet bruger vi standardindstillingen for
    # "ucph-revy.cls", at "aktoversigt.plan" ligger i samme mappe som
    # .tex-filen selv. Derfor fjerner vi bare indstillingen
    # "planfile=../aktoversigt.plan". I stedet laver vi nye
    # "aktoversigt.plan"-filer i undermapperne med .tex-filer (nok
    # "sange" og "sketches") som peger på de andre .tex-filer inde fra
    # de mapper.

    # Den primære aktoversigt vil så stadig være den i rodmappen. Hvis
    # den bliver lavet om, så skal den her funktion køres igen, for at
    # opdatere de ekstra aktoversigter i undermapperne.
    cmd = "overleaf-compat"
    doc = "Strukturér, så registermærkninger også virker på Overleaf."
    warn = """
Husk, at køre med overleaf-compat igen, hvis du skriver om
i atkoversigt.plan.
"""

    def clobber( tex, revue ):
        try:
            i,line = find_documentclass( tex.info['tex'] )
        except StopIteration:
            return tex
        tex.info['tex'][i] = re.sub(
            r"(documentclass\[[^]]*)planfile=[^],]*",
            "\\1",
            line,
            count = 1
        )

        # den nye "aktoversigt.plan" fil:
        materials = [material for act in revue.acts
                     for material in act.materials ]
        matdirs = set([ os.path.dirname( material.path )
                        for material in materials ]
                      )
        dir_firsts = [ next( material.path for material in materials
                             if os.path.dirname( material.path ) == matdir )
                       for matdir in matdirs ]
        for first in dir_firsts:
            if os.path.samefile( first, tex.fullpath ):
              out = []
              with open("aktoversigt.plan", "r", encoding="utf-8") as plan:
                    for line in plan.readlines():
                        if line.endswith( ".tex\n" ):
                            out += ( os.path.relpath(
                                os.path.abspath( line ),
                                start=os.path.dirname( tex.fullpath )
                            ) ).replace( "\\", "/" )
                        else:
                            out += line 
              with open( os.path.join( os.path.dirname( first ),
                                       "aktoversigt.plan" ),
                         "w", encoding="utf-8" ) as outf:
                  outf.write( "".join( out ) )
                                
        return tex

clobber_steps = {
    # måske de er en bedre måde at strukturere det her på, efter cmd
    # og doc blev indført...?
    step.cmd: step for step in ClobberInstructions.__subclasses__()
}

def clobber_my_tex( revue, args ):
    "Methods that rewrite your tex files."
    
    initresults = { cmd: clobber_steps[ cmd ].init( revue )
                    for cmd in clobber_steps if cmd in args
    }
    cont = "y" if revue.conf.conf.getboolean( "Behaviour", "always say yes",
                                              fallback = False ) \
        else input(
                stoptext.format(
                    "\n".join(
                        "  " + arg for arg in clobber_steps if arg in args
                    ),
                    "\n".join([
                        clobber_steps[ arg ].warn for arg in clobber_steps if (
                            arg in args
                            # ingen linjeskift for tomme strenge
                            and clobber_steps[ arg ].warn 
                        )
                    ]) + "\n" )
        )
    
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

