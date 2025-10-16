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
from typing import Optional, Any
from collections.abc import Callable
from configparser import NoSectionError

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
from ninja_wizard import ninja_wizard

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

    processes = int( conf["Behaviour"]["max_proc"] )
    if processes <= 1:
        rs = [ cv.tex_to_wordcount( mat ) for mat in revue.materials ]
    else:
        with Pool( processes = processes ) as pool,\
             PoolOutputManager() as man:
            po = man.PoolOutput( pool._processes )
            po.queue_add( *( cv.task_name( mat ) for mat in revue.materials ) )
            counting = pool.starmap_async(
                cv.tex_to_wordcount, ((mat,po,conf) for mat in revue.materials )
            )
            while not counting.ready():
                sleep( 1 )
                po.refresh()
            po.end_output()
            rs = counting.get()

    counts, error, warning, success, skip = [],[],[],[],[]
    for r,m,i in zip( rs, revue.materials, cycle( indices ) ):
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
            *( ( len( fn ) + 3, task_start( ind + ": " ) + fn )
               for fn, ind in  error
              )
        )
    if warning:
        print( "\nOrdtælling blev fuldført i følgende filer, men med "\
               + text_effect( "LaTeX-advarsler", "warn" ) + ":"
              )
        print_columnized(
            *( ( len( fn ) + 3, task_start( ind + ": " ) + fn )
               for fn, ind in warning
              )
        )
    if error or warning:
        print( "Logfiler fra LaTeX findes i " + conf["Paths"]["tex cache"] )
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

    for mat, count in zip( revue.materials, counts ):
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

def plan_file( planfile = "aktoversigt.plan" ):
    try:
        sf.create_plan_file( planfile )
    except FileExistsError:
        pass
    else:
        print("Plan file '{}' created successfully.".format( planfile )),
        print("You probably want to rearrange its contents "\
              "before continuing.\n"),
        raise ExitOnStopArgument( plan )

class SMP(Callable):
    def fail( *_ ):
        raise ValueError(
            "Conflicting commands for number of parallel processes."
        )
    def succeed( self, n ):
        conf.conf.set( "Behaviour", "max_proc", str( n ) )
        self.do = self.fail
    def __init__( self ):
        try:
            self.succeed( cpu_count() )
        except NoSectionError:
            conf.conf.add_section( "Behaviour" )
            self.succeed( cpu_count() )
        self.do = self.succeed
    def __call__( self, n ):
        self.do( n )
set_max_parallel = SMP()

@dataclass
class Argument:
    cmd: str
    doc: str
    action: Callable[..., Any]
    flag: Optional[ str ] = None

def write_help(*args):
    print("TeX et revymanus.\n\nSyntaks:\n\n[pyton] create.py [-", end="")
    have_flags = [ arg for arg in all_possible_args if arg.flag ]
    for flag in have_flags:
        print("[{}]".format(flag.flag), end="")
    print("] ", end="")
    for toggle in toggles:
        print("[{}] ".format(toggle.cmd), end="")
    print( "[--<tilvalg>=<ny indstilling>] ", end="" )
    print("[ <kommandoer> ] [ <planfil> ]")
    print("""
Som standard, hvis der ikke gives nogen kommandoer, lader scriptet som om
det har fået kommandoerne
   """, end="")
    print( " ".join( default_commands ), end="" )
    print( """

Kommandoen "manus" er det samme som at give kommandoerne
   """, end="")
    print( " ".join( manus_commands ), end="" )
    print( "\nHvis ingen planfil angives, går scriptet ud fra, at den hedder")
    print( "\n  aktoversigt.plan" )
    print( """

Hele listen med kommandoer er:

Flag:""")
    for flag in have_flags:
        print("  -{:<17} {}".format(flag.flag, flag.doc))
    print("\nTilvalg:")
    for toggle in toggles + set_toggles:
        print("  {:<18} {}".format(toggle.cmd, toggle.doc))
    print("\nKommandoer:")
    for action in actions:
        print("  {:<18} {}".format(action.cmd, action.doc))
    print("\nKommandoer, der skriver om i TeX-filerne:")
    for clobber in clobber_steps:
        print("  {:<18} {}".format(clobber_steps[ clobber ].cmd,
                                  clobber_steps[ clobber ].doc)
              )

    print("\nTilvalg, som kan tilsidesætte indstillinger i revytex.conf:")
    for setting in settings:
        if setting not in role_settings:
            print("  {:<18} {}".format( setting.cmd + "=", setting.doc ) )
    print()
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
    raise ExitOnStopArgument( help_arg )

plan = Argument( "plan",
                 "Lav en ny aktoversigt.plan ud fra mappens nuværende indhold.",
                 plan_file
                )

actions = [ plan ] + [
    Argument( "manus",
              "TeX'er kun det overordnede manus (se ovenfor)",
              lambda: None      # handled specially in create()
             ),
    
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

    Argument( "timesheet",
              "Lav et tidsdiagram, som kan hjælpe med at lægge ninjaplanen.",
              lambda: tex_queue.append(( TeX( revue ).create_timesheet(),
                                         "tidsdiagram.pdf","",3
                                         # kør tex 3 gange, fordi vi laver
                                         # unoder med tikZ
                                        ))
              ),

    Argument( "ninjaplan",
              "Lav en sceneskiftplan, ud fra '\\ninja'-makroer i .tex-filerne.",
              lambda: tex_queue.append(( TeX( revue ).create_ninja_plan(),
                                         "ninjaplan.pdf"
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
             ),

    Argument( "ninja-wizard",
              "Interaktiv hjælp til at skrive ninjaplaner.",
              lambda: ninja_wizard( revue )
             ),
    ]

def execute_commands(revue, args):
    if any( x in args for x in clobber_steps ):
        clobber_my_tex( revue, args )

    for action in actions:
        if action.cmd in args:
            action.action()

def tex_all():
    conf.conf.set( "TeXing", "force TeXing of all files", "yes" )

def verbose():
    conf.conf.set( "TeXing", "verbose output", "yes" )

help_arg = Argument( "--help",
                     "Du kan få hjælp",
                     write_help,
                     flag = "h"
                    )

toggles = [ help_arg ] + [
    Argument( "--tex-all",
              "TeX alt! (ligesom indstillingen i revytex.conf)",
              tex_all
              ),
    Argument( "--single-thread",
              "Brug ikke parallelkørsel.",
              lambda: set_max_parallel( 1 ),
              "s"
             )
    ]

set_toggles = [ Argument( "--max-parallel=",
                          "Sæt max antal parallelle processer (min. 1).",
                          set_max_parallel
                         )
                ]

flags = [
    Argument( "v",
              "Få mere verbost output fra LaTeX.",
              verbose,
              flag = "v"
             ),
    Argument( "y",
              "Sig ja til alt.",
              lambda: conf.conf.set( "Behaviour", "always say yes", "yes" ),
              flag = "y"
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

settings = role_settings + [
    Argument(
        "--roles-sheet-fn",
        "Filnavn til output af rolle-oversigts-regneark fra roles-sheet.",
        lambda fn: conf.conf.set( "Files", "roles sheet output",
                                  str( Path( fn ) )
                                 )
    ),
    Argument(
        "--latex-command",
        "Brug en anden latex-kommando (end pdflatex).",
        lambda fn: conf.conf.set( "TeXing", "latex command", fn.strip() )
    ),
    Argument(
        "--ninja-yaml",
        "Filnavn til ninja-yaml-filen.",
        lambda fn: conf.conf.set( "Files", "ninja yaml", str( Path( fn ) ) )
    )
]
 
all_possible_args = actions + toggles + flags + settings

default_commands = (tuple() if conf.getboolean("TeXing","skip thumbindex")
                    else ("thumbindex",)) +\
    ("aktoversigt", "roles", "frontpage", "props", "contacts", "material",
     "individual", "songmanus", "manus")
manus_commands = (tuple() if conf.getboolean("TeXing","skip thumbindex")
                    else ("thumbindex",)) +\
    ("aktoversigt", "roles", "frontpage", "props", "contacts", "material")

            
def create( *arguments ):

    planfile = Path( "aktoversigt.plan" )
    known_flags = [ cmd.flag for cmd in all_possible_args if cmd.flag ]
    wrong_args, wrong_flags = [], []
    for arg in arguments:
        if re.match( "-[a-z]", arg ):
            wrong_flags += [ f for f in arg[1:] if not f in known_flags ]
        elif arg not in \
             list( clobber_steps ) + [ a.cmd for a in all_possible_args ]:
            wrong_args += [ arg ]
    if wrong_args:
        for wrong in wrong_args:
            prop_path = Path( wrong )
            if prop_path.exists() or prop_path.suffix == ".plan":
                planfile = Path( wrong )
        try:
            wrong_args.remove( str( planfile ) )
        except ValueError:
            # der var ikke nogen
            pass
    if wrong_args:        # still...
        print( "These arguments were not recognized, and will be ignored:" )
        print( "    ", end="" )
        for wrong in wrong_args:
            print( wrong, end="  " )
        print()
    if wrong_flags:
        print("These flag were not recognized, and will be ignored:  ", end="")
        for wrong in wrong_flags:
            print( wrong, end=" " )
        print()
    if wrong_flags or wrong_args:
        print()
    
    # (Re)initialize:
    conf.load("revytex.conf")
    conf.add_args([ x for x in arguments if x[0] != "-" ])
    tex_queue.clear()
    merge_queue.clear()
    set_max_parallel.__init__()
    
    for toggle in toggles:
        if toggle.cmd in arguments:
            toggle.action()
    for arg in arguments:
        for setting in settings + set_toggles:
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
    for flag in all_possible_args:
        if flag.flag and flag.flag in \
           "".join( [ match[1] for match in
                      [ re.match( r"^-([^-]+)", arg ) for arg in arguments ]
                      if match ]
                     ):
            flag.action()

    global revue                # TODO: EVIL! :hiss:
    if not planfile.exists():
        plan_file( planfile )
    revue = cr.Revue.fromfile( planfile )
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

    processes = min( int(conf["Behaviour"]["max_proc"]),
                     max( len( tex_queue ), len( merge_queue ) )
                    )
    if processes <= 1:
        rs = [ cv.tex_to_pdf( *tex_args ) for tex_args in tex_queue ]
        if any( isinstance( r, Exception ) for r in rs ):
            print("Some TeX files failed to compile. "\
                      "Can't create manuscripts.")
            print("Find TeX logfiles in {}".format(conf["Paths"]["tex cache"]) )
            return
        rs = []
        for merge_arg in merge_queue:
            try:
                rs += [ PDF().pdfmerge( *merge_arg ) ]
            except Exception as e:
                rs += [ e ]
        if any( isinstance( r, Exception ) for r in rs ):
            print( "There was an error compiling or optimizing some pdfs." )
            print( "Some target pdfs may not have been created." )
            return
    else:
        with Pool( processes = processes ) as pool:
            if tex_queue:
                try:
                    print( "\n\033[1mTeXification:\033[0m" )
                    cv.submit_parallel_tex_to_pdf( pool, tex_queue )
                except ProcessError:
                    print("Some TeX files failed to compile. "\
                          "Can't create manuscripts.")
                    return
            if merge_queue:
                try:
                    print( "\n\033[1mCollationizionation:\033[0m" )
                    PDF().submit_parallel_pdfmerge( pool, merge_queue )
                except ProcessError:
                    print( "There was an error compiling or optimizing "\
                           "some pdfs." )
                    print( "Some target pdfs may not have been created." )
                    return
    	
    print("Nothing seems to have gone wrong!")

if __name__ == "__main__":
    try:
        create( *(sys.argv[1:]) )
    except ExitOnStopArgument:
        pass
