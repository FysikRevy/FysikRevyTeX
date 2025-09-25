# encoding: utf-8
import re
import os
import string
from operator import itemgetter
from pathlib import Path
from enum import Flag, auto

from base_classes import Role, NinjaProp
from tex import TeX

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
        from roles_reader import formats

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
                "roles": scorechart[ best ][ "roles" ],
                "instructors": scorechart[ best ].get( "instructors", None )
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
                 [ translations[t][ "roles" ],
                   translations[t].get( "instructors", None )
                  ]
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
                *(translations[ tex.info[ "title" ]])
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

# --- Hjælpefunktioner til klasse-valgmuligheder:

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
        try:
            planpath = Path( revue.planfile ).resolve()
        except AttributeError:
            planpath = Path( "aktoversigt.plan" ).resolve()
        planpath = planpath\
            .relative_to( Path( tex.fullpath ).parent )\
            .as_posix()
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
i din planfil.
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
              with open(revue.planfile, "r", encoding="utf-8") as plan:
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

class InsertNinjas( ClobberInstructions ):
    cmd = "insert-ninjas"
    doc = "Overfør ninjaplan fra yaml-fil til tex-filerne."

    def init( revue ):
        from ruamel.yaml import YAML
        yaml=YAML()
        with open( revue.conf["Files"]["ninja yaml"], "r", encoding="utf-8" )\
             as f:
            ninja_info = yaml.load( f )
        mat_paths = {
            str( Path.cwd() / mat.path ): mat
            for mat in revue.materials
        }
        changed_ninjas = [
            info for info in ninja_info
            if info['rekvisitter'] != \
              ([ prop.to_serializable()
                 for prop in \
                 mat_paths[ str( Path.cwd() / info['fil'] ) ].ninjaprops
                ] if mat_paths[ str( Path.cwd() / info['fil'] ) ].ninjaprops\
                     != None \
                  else None
               )
        ]
        print( [([ prop.to_serializable()
                 for prop in \
                 mat_paths[ str( Path.cwd() / info['fil'] ) ].ninjaprops
                ] if mat_paths[ str( Path.cwd() / info['fil'] ) ].ninjaprops\
                     != None \
                  else None
               ) for info in ninja_info ] )
        print( [ info['rekvisitter'] for info in ninja_info ] )

        if not changed_ninjas:
            print( "" )
            print( "No changes detected in {}. The step `insert-ninjas` "
                   "will be skipped."\
                   .format( revue.conf["Files"]["ninja yaml"] )
                  )
            clobber_steps[ "insert-ninjas" ] = ClobberInstructions
            return

        if any( info['rekvisitter'] for info in changed_ninjas ):
            print( "" )
            print("These materials will have ninja information "
                  "added or changed:")
            print("-----------------------------------------------\n")
            for info in changed_ninjas:
                if info['rekvisitter']:
                    print( "  " + info['fil'] )

        if any( not info['rekvisitter'] for info in changed_ninjas ):
            print( "" )
            print("These materials will have their ninja information removed:")
            print("-----------------------------------------------\n")
            for info in changed_ninjas:
                if not info['rekvisitter']:
                    print( "  " + info['fil'] )

        return changed_ninjas

    def clobber( tex, changed_ninjas ):
        clobber_path = Path( tex.fullpath )
        try:
            prop_cmd = next(
                [ "\\ninjas{" ] \
                + [ "  " + line
                    for prop in info['rekvisitter']
                    for line in  NinjaProp.from_deserialized( prop ).tex_cmd()
                   ] \
                + [ "}" ]
                for info in changed_ninjas
                if Path.cwd() / info['fil'] == clobber_path
            )
            return replace_ninjas( tex, prop_cmd )
        except StopIteration:
            if tex.info['ninjaprops']:
                return replace_ninjas( tex, [ "" ] )
            else:
                return tex

class RemoveNinjas( ClobberInstructions ):
    cmd = "remove-ninjas"
    doc = "Fjern \\ninjas-kommandoer i alle .tex-filer"

    def clobber( tex, _ ):
        return replace_ninjas( tex, [ "" ] )

def replace_ninjas( tex, prop_cmd ):
    lines = ( n_l for n_l in enumerate(tex.info['tex']) )
    # men hvad hvis der ikke er nogen!?!
    try:
        ninjal, ninjaline = next( (n,l) for (n,l) in lines
                                  if "\\ninjas" in l
                                 )
    except StopIteration:
        # ingen `\ninjas` i forvejen. Sæt ind efter `\maketitle`
        # eller `\begin{document}`
        def look_for_spaces():
            nonlocal bookends, ninjac, ninjal
            whiterun = re.match( r"\s*", l[ ninjac : ] )
            bookends += whiterun[0]
            ninjac += whiterun.end()
            if ninjac == len( l ):
                # keep looking in the next line
                ninjac = 0
                return looking_for
            ninjal = n
            return looking_for & ~LookingFor.NONSPACE
        class LookingFor( Flag ):
            BEGIN = auto()
            MAKETITLE = auto()
            NONSPACE = auto()

        looking_for = LookingFor.BEGIN | LookingFor.MAKETITLE
        for (n,l) in enumerate( tex.info['tex'] ):
            if LookingFor.NONSPACE in looking_for:
                looking_for = look_for_spaces()
                if LookingFor.NONSPACE in looking_for:
                    continue
            if LookingFor.BEGIN in looking_for:
                try:
                    ninjac = l.index( "\\begin{document}" ) \
                           + len( "\\begin{document}" )
                except ValueError:
                    pass
                else:
                    try:
                        indent = (
                            re.search(
                                r"\\begin{document}[^\S\n]*\s*?([^\S\n]*)\S", l
                            ) or next( re.search( r"^([^\S\n]*)\S", l, re.M )
                                       for l in tex.info['tex'][ n : ]
                                       if re.search( r"\S", l )
                                      )
                        )[1]
                    except StopIteration:
                        indent = ""
                    ninjal = n
                    looking_for = \
                        looking_for & ~LookingFor.BEGIN | LookingFor.NONSPACE
            if LookingFor.MAKETITLE in looking_for and "\\maketitle" in l:
                mt_re = re.search( r"((?:^[^\S\n]*)?)\\maketitle", l, re.M )
                indent = mt_re[1]
                ninjac = mt_re.end()
                ninjal = n
                looking_for = \
                    looking_for & ~LookingFor.MAKETITLE | LookingFor.NONSPACE
            if LookingFor.NONSPACE in looking_for:
                bookends = ""
                looking_for = look_for_spaces()
            if not looking_for:
                break
        try:
            endc = ninjac
            endl = ninjal
        except NameError:
            print( "Couldn't find `document` environment. Skipping file:" )
            print( "  {}".format( clobber_path.relative_to( Path.cwd() ) ) )
            return tex
    else:
        ninjac = ninjaline.find( "\\ninjas" )
        endl = ninjal
        endc = ninjaline.find( "{", ninjac )
        line = ' ' * endc + ninjaline[ endc + 1 : ]
        bookends = ""
        indent = re.search( r"((?:^[^\S\n]*)?)\\ninjas", ninjaline,
                            flags = re.MULTILINE
                           )[1]
        try:
            if endc > 0:
                depth = 1
            else:
                raise StopIteration

            while True:
                for (i,c) in enumerate( line ):
                    endc = i
                    if depth <= 0:
                        if c in string.whitespace:
                            bookends += c
                        else:
                            break
                    elif c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                else:           # didn't hit break
                    endl, line = next( lines )
                    continue
                break
        except StopIteration:
            print("Couldn't find end of `\\ninjas` command. Skipping file:")
            print("  {}".format( clobber_path.relative_to( Path.cwd() ) ) )
            return tex

    if prop_cmd == [""]:
        bookends = ""

    new_tex = tex.info['tex'][0:ninjal]
    new_tex += [ tex.info['tex'][ninjal][:ninjac] + prop_cmd[0] + "\n" ]
    for cmd_l in prop_cmd[1:]:
        new_tex += [ indent + cmd_l + "\n" ]
    new_tex[-1] = new_tex[-1][:-1] + bookends + tex.info['tex'][endl][ endc : ]
    new_tex += tex.info['tex'][ endl + 1 : ]

    tex.info['tex'] = new_tex
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

    active_steps = { arg: clobber_steps[ arg ] for arg in clobber_steps
                     if arg in args \
                     and clobber_steps[ arg ] != ClobberInstructions
                    }
    if not active_steps:
        return
    
    cont = "y" if revue.conf.conf.getboolean( "Behaviour", "always say yes",
                                              fallback = False ) \
        else input(
                stoptext.format(
                    "\n".join(
                        "  " + arg for arg in active_steps
                    ),
                    "\n".join([
                        active_steps[ arg ].warn for arg in active_steps if \
                            active_steps[ arg ].warn 
                            # ingen linjeskift for tomme strenge
                    ]) + "\n" )
        )
    
    if cont == 'y':
        tex = TeX( revue )
        for material in [ material for act in revue.acts
                          for material in act.materials ]:
            fname = material.path
            tex.parse( fname )
            for cmd in active_steps:
                tex = active_steps[ cmd ].clobber(
                    tex, initresults[ cmd ]
                )
            tex.write( fname )
            material.modification_time = tex.info[ "modification_time" ]

