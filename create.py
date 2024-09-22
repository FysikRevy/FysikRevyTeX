#!/usr/bin/env python3
# coding: utf-8
import glob
import os
import sys
import re
sys.path.append("scripts")
from multiprocessing import Pool, cpu_count, ProcessError
from pathlib import Path
from time import sleep
from itertools import cycle
from dataclasses import dataclass

import classy_revy as cr
import setup_functions as sf
import converters as cv
import config as cf
from tex import TeX
from clobberers import clobber_steps, clobber_my_tex
from pdf import PDF
import roles_reader
from pool_output import \
    PoolOutputManager, Output, indices, task_start, \
    text_effect, print_columnized

from config import configuration as conf

class ExitOnStopArgument( Exception ):
    pass

tex_queue, merge_queue = [],[]

@dataclass
class Content:
    pdfname: str
    bookmark: str
    start_verso: bool = False
    rel_dir: Path = Path( conf["Paths"]["pdf"] )

    @property
    def merge_args( self ):
        return ( str( self.rel_dir / self.pdfname ),
                      self.bookmark, self.start_verso
                )

    def tex_args( self, subtitle ):
        return (
            TeX( revue ).create_frontpage( subtitle=subtitle ),
            self.pdfname, str( self.rel_dir )
        )

class Contents:
    frontpage = Content( "frontpage.pdf", "Forside" )
    roles = Content( "rolleliste.pdf", "Rolleliste", True )
    aktoversigt = Content( "aktoversigt.pdf", "Aktoversigt" )
    thumbindex = Content( "thumbindex.pdf", "Registerindeks" )
    contacts = Content( "kontaktliste.pdf", "Kontaktliste" )

    def __init__( self,
                  materials,
                  frontpage = None,
                  include = [],
                  exclude = []
                 ):
        self.include = include
        self.exclude = exclude
        self.materials = materials
        if frontpage:
            if not isinstance( frontpage, Content ):
                raise TypeError( "Argument frontpage most be a Content.",
                                 frontpage
                                )
            self.frontpage = frontpage
            if self.include:
                self.include += [ frontpage ]

    @property
    def before( self ):
        return ( self.frontpage, self.roles, self.aktoversigt, self.thumbindex )

    @property
    def after( self ):
        return ( self.contacts, )

    @property
    def arglist( self ):
        if conf.getboolean( "TeXing", "skip thumbindex" ):
            self.exclude = [ self.thumbindex ] + [ x for x in self.exclude ]

        def filtered_arglists( contents ):
            return ( content.merge_args for content in contents
                     if content not in self.exclude
                     and not self.include or content in self.include
                    )

        yield from filtered_arglists( self.before )
        yield self.materials
        yield from filtered_arglists( self.after )

    def queue_tex_frontpage( self, subtitle = "\\TeX{}ster" ):
        tex_queue.append( self.frontpage.tex_args( subtitle ) )
        return self

    def queue_merge( self, pdfname ):
        merge_queue.append(( [contents for contents in self.arglist],
                             pdfname
                            ))
        return self

def roles_csv():

    print( "\n\033[1mOrdtælling:\033[0m" )

    mats = [ mat for act in revue.acts for mat in act.materials ]
    
    with Pool( processes = cpu_count() ) as pool,\
         PoolOutputManager() as man:
        po = man.PoolOutput( cpu_count() )
        po.queue_add( *( cv.task_name( mat ) for mat in mats ) )
        counting = pool.starmap_async( cv.tex_to_wordcount,
                                       ( (mat,po,conf) for mat in mats )
                                      )
        while not counting.ready():
            sleep( 1 )
            po.refresh()
        po.end_output()
        rs = counting.get()

    counts, error, warning, success, skip = [],[],[],[],[]
    for r,m,i in zip( rs, mats, cycle( indices ) ):
        f = Path( m.path ).name
        match r[0]:
            case Exception():
                error += [ (f,i) ]
            case 0:
                success += [ (f,i) ]
            case None:
                skip += [ (f,i) ]
            case _:
                warning += [ (f,i) ]
        counts += [ r[1] ]
    if error:
        print( "\nOrdtælling mislykkedes i følgende filer pga. "\
               + text_effect( "LaTeX-fejl", "error" ) + ":"
              )
        print_columnized(
            *( ( len( fn.name ) + 3, task_start( ind + ": " ) + fn.name )
               for fn, ind in  error
              )
        )
    if warning:
        print( "\nOrdtælling blev fuldført i følgende filer, men med "\
               + text_effect( "LaTeX-advarsler", "warn" ) + ":"
              )
        print_columnized(
            *( ( len( fn.name ) + 3, task_start( ind + ": " ) + fn.name )
               for fn, ind in warning
              )
        )
    print()
    if success:
        print( "Ordtælling blev " \
               + text_effect( "fuldført korrekt", "success" )\
               + " i {} filer.".format( len( success ) )
              )
    if skip:
        print( "{} filer er ikke opdateret, og den nye ".format( len( skip ))\
               + "ordtælling blev " + text_effect( "sprunget over", "skip" )\
               + "."
              )

    for mat, count in zip( mats, counts ):
        mat.wordcounts = count

    o = Output()
    try:
        fn = conf["Files"]["roles sheet output"]
    except KeyError:
        o.begin( 0, "roles.csv (default name, can be set in revytex.conf)" )
        revue.write_roles_csv()
    else:
        o.begin( 0, fn )
        revue.write_roles_csv( fn )
    o.success( 0 )

def google_forms_signup():
    from google_forms_signup import create_new_form
    create_new_form( revue )

class Argument:
    def __init__(self, cmd, doc, action):
        self.cmd = cmd
        self.doc = doc
        self.action = action

def write_help(*args):
    print("TeX et revymanus.\n\nSyntaks:\n\n[pyton] create.py [-", end="")
    for flag in flags:
        print("[{}]".format(flag.cmd), end="")
    print("] ", end="")
    for toggle in toggles:
        print("[{}] ".format(toggle.cmd), end="")
    print( "[--<tilvalg>=<ny indstilling>] ", end="" )
    print("[ <kommandoer> ]")
    print("""
Som standard, hvis der ikke gives nogen kommandoer, lader scriptet som om
det har fået kommandoerne
   """, end="")
    print( " ".join( default_commands ), end="" )
    print( """

Kommandoen "manus" er det samme som at give kommandoerne
   """, end="")
    print( " ".join( manus_commands ), end="" )
    print( """

Hele listen med kommandoer er:

Flag:""")
    for flag in flags:
        print("  -{:<17} {}".format(flag.cmd, flag.doc))
    print("\nTilvalg:")
    for toggle in toggles:
        print("  {:<18} {}".format(toggle.cmd, toggle.doc))
    print("\nKommandoer:", end="")
    print("""
  manus              TeX'er kun det overordnede manus (se ovenfor)
  plan               Laver en ny aktoversit.plan""")
    for action in actions:
        print("  {:<18} {}".format(action.cmd, action.doc))
    print("\nKommandoer, der skriver om i TeX-filerne:")
    for clobber in clobber_steps:
        print("  {:<18} {}".format(clobber_steps[ clobber ].cmd,
                                  clobber_steps[ clobber ].doc)
              )

    print("\nTilvalg, som kan tilsidesætte indstillinger i revytex.conf:")
    print("""\
De her sætter filnavnet for rollefordelingsfiler med et bestemt
format. Argumentet efter =-tegnet skal være stien til filen. Fx:
    --{}=./{}
""".format( roles_reader.formats[0].name,
            roles_reader.formats[0].default_filename
           )
          )
    for setting in role_settings:
          print("  {:<18} {}".format( setting.cmd + "=", setting.doc ) )

    print()
    for setting in settings:
        if setting not in role_settings:
            print("  {:<18} {}".format( setting.cmd + "=", setting.doc ) )
    print()
    raise ExitOnStopArgument

actions = [
    Argument( "aktoversigt",
              "TeX en ny aktoversigt",
              lambda: tex_queue.append(( TeX( revue ).create_act_outline(),
                                         Contents.aktoversigt.pdfname
                                        ))
             ),

    Argument( "roles",
              "TeX en ny rolleliste",
              lambda: tex_queue.append(( TeX( revue ).create_role_overview(),
                                         Contents.roles.pdfname
                                        ))
             ),

    Argument( "frontpage",
              "TeX en ny forside",
              lambda: tex_queue.append(( TeX( revue ).create_frontpage(),
                                         Contents.frontpage.pdfname
                                        ))
             ),
    
    Argument( "thumbindex",
              "TeX et nyt registerindeks",
              lambda: tex_queue.append(( TeX( revue ).create_thumbindex(),
                                         Contents.thumbindex.pdfname
                                        ))
             ),

    Argument( "props",
              "Opdater rekvisitliste i Google Sheets (hvis det er sat op)",
              lambda: TeX( revue ).create_props_list()
              # TODO: måske hører den funktion ikke hjemme i tex længere?
             ),
              
    Argument( "contacts",
              "TeX en ny kontaktliste",
              lambda: tex_queue.append((
                  TeX( revue ).create_contacts_list(conf["Files"]["contacts"]),
                  Contents.contacts.pdfname
              ))
             ),
    
    Argument( "material",
              "Gen-TeX materialesiderne (hvis de er blevet ændret)",
              lambda: tex_queue.extend( (mat,) for mat in revue.materials )
             ),

    Argument( "individual",
              "Sammensæt nye individuelle manuskripter (hvis der er ændringer)",
              lambda: [
                  Contents( materials = actor,
                            frontpage = Content(
                                "forside-{}.pdf".format( actor.name ),
                                "Forside",
                                rel_dir = Path( conf["Paths"]["pdf cache"] )
                            )
                           )\
                      .queue_tex_frontpage( subtitle = actor.name )\
                      .queue_merge(
                          str(
                              Path( conf["Paths"]["individual pdf"] )\
                              / "{}.pdf".format( actor.name )
                          )
                      )
                  for actor in revue.actors
              ]
             ),

    Argument( "songmanus",
              "Sammensæt et nyt sangmanuskript (hvis der er ændringer)",
              lambda: Contents(
                  materials = [
                      m for m in revue.materials
                      if m.category == conf["Paths"]["songs"]
                  ],
                  frontpage = Content( "sangforside.pdf", "Forside" )
              ).queue_tex_frontpage( subtitle = "sangmanuskript" )\
               .queue_merge( str( Path( conf["Paths"]["pdf"] )\
                                  / "sangmanuskript.pdf"
                                 )
                            )
              ),

    Argument( "signup",
              "TeX en ny tilmeldingsblanket",
              lambda: tex_queue.append(( TeX( revue ).create_signup_form(),
                                         "rolletilmelding.pdf"
                                        ))
             ),

    Argument( "roles-sheet",
              "Lav en csv(/tsv) fil med en oversigt over rollerne.",
              roles_csv
              ),

    Argument( "google-forms-signup",
              "Skriv roller og revydage ind i en Google Forms tilmeldingsformular.",
              google_forms_signup
             )
    ]

def execute_commands(revue, args):
    if any( x in args for x in clobber_steps ):
        clobber_my_tex( revue, args )

    for action in actions:
        if action.cmd in args:
            action.action()

def tex_all(conf):
    conf["TeXing"]["force TeXing of all files"] = "yes"

def verbose(conf):
    conf["TeXing"]["verbose output"] = "yes"

toggles = [
    Argument( "--help",
              "Du kan få hjælp",
              write_help
              ),
    Argument( "--tex-all",
              "TeX alt! (ligesom indstillingen i revytex.conf)",
              tex_all
              )
    ]

flags = [
    Argument( "h",
              "Jeg har hjælp til dig",
              write_help
             ),
    Argument( "v",
              "Få mere verbost output fra LaTeX.",
              verbose
             ),
    Argument( "y",
              "Sig ja til alt.",
              lambda: conf.conf.set( "Behaviour", "always say yes", "yes" )
             )
    ]

def config_setter_for_format( form ):
    return lambda setting: \
        conf.conf.set( "Files", form.name, str( Path( setting ) ))

role_settings = [
    Argument( "--" + form.name,
              form.description,
              config_setter_for_format( form )
             ) for form in roles_reader.formats
]

roles_sheet_filename = Argument(
    "--roles-sheet-fn",
    "Filnavn til output af rolle-oversigts-regneark fra roles-sheet.",
    lambda fn: conf.conf.set( "Files", "roles sheet output", str( Path( fn ) ) )
)

settings = role_settings + [ roles_sheet_filename ]

default_commands = (tuple() if conf.getboolean("TeXing","skip thumbindex")
                    else ("thumbindex",)) +\
    ("aktoversigt", "roles", "frontpage", "props", "contacts", "material",
     "individual", "songmanus", "manus")
manus_commands = (tuple() if conf.getboolean("TeXing","skip thumbindex")
                    else ("thumbindex",)) +\
    ("aktoversigt", "roles", "frontpage", "props", "contacts", "material")

            
def create( *arguments ):

    unkw_warn = ( x for x in 
        [ "These arguments were not recognized, and will be ignored:" ] )
    for arg in arguments:
        if arg not in list( clobber_steps ) + actions + flags + settings\
           and not re.match( "-[a-z]", arg ):
            try:
                print( next( unkw_warn ) )
            except StopIteration:
                pass
            print( "  " + arg, end="" )
    try:
        next( unkw_warn )
    except StopIteration:
        print( "\n" )
    
    # Load configuration file:
    conf.load("revytex.conf")
    conf.add_args([ x for x in arguments if x[0] != "-" ])
    tex_queue.clear()
    merge_queue.clear()
    
    for toggle in toggles:
        if toggle.cmd in arguments:
            toggle.action(conf)
    for arg in arguments:
        for setting in settings:
            if arg.startswith( setting.cmd ):
                try:
                    setting.action( arg.split( "=", maxsplit=1 )[1] )
                except IndexError:
                    print(
                        "Fejl: {} skal have en indstilling, som skrives som:"\
                        .format( setting.cmd )
                    )
                    print( "          '{}=<indstilling>' (uden mellemrum)."\
                           .format( setting.cmd, setting.cmd )
                    )
                    raise ValueError
    for flag in flags:
        if flag.cmd in \
           "".join( [ match[1] for match in
                      [ re.match( r"^-([^-]+)", arg ) for arg in arguments ]
                      if match ]
                     ):
            flag.action(conf) 

    if "plan" in arguments or not os.path.isfile("aktoversigt.plan"):
        sf.create_plan_file("aktoversigt.plan")
        print("Plan file 'aktoversigt.plan' created successfully.")
        print("You probably want to rearrange its contents before continuing.")
        raise ExitOnStopArgument

    global revue                # TODO: EVIL! :hiss:
    revue = cr.Revue.fromfile("aktoversigt.plan")
    path = revue.conf["Paths"]
    conv = cv.Converter()

    if all( arg[0] == "-" for arg in arguments ):
        arguments = default_commands
    elif "manus" in arguments:
        arguments += manus_commands

    execute_commands( revue, arguments )
    if "manus" in arguments:
        Contents( materials = revue )\
            .queue_merge( str( Path( path["pdf"] ) / "manuskript.pdf" ) )

    try:
        print( "\033[1mTeXification:\033[0m\n" )
        cv.parallel_tex_to_pdf( tex_queue )
    except ProcessError:
        print( "Some TeX files failed to compile. Can't create manuscripts.")
        return
    try:
        print( "\033[1mCollationizionation:\033[0m\n" )
        PDF().parallel_pdfmerge( merge_queue )
    except ProcessError:
        print( "There was an error compiling or optimizing some pdfs." )
        print( "Some target pdfs may not have been created." )
        return
    	
    print("Nothing seems to have gone wrong!")

if __name__ == "__main__":
    try:
        create( *(sys.argv[1:]) )
    except ExitOnStopArgument:
        pass
