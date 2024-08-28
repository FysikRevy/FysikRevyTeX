#!/usr/bin/env python3
# coding: utf-8
import glob
import os
import sys
import re
sys.path.append("scripts")
from multiprocessing import Pool
from pathlib import Path

import classy_revy as cr
import setup_functions as sf
import converters as cv
import config as cf
from tex import TeX
from clobberers import clobber_steps, clobber_my_tex
from pdf import PDF
import roles_reader

from config import configuration as conf

def create_material_pdfs(revue):
    file_list = []
    for act in revue.acts:
        for material in act.materials:
            file_list.append(material)

    conv = cv.Converter()
    conv.parallel_textopdf(file_list)
    # for f in file_list:
    #    conv.textopdf(f)

def create_individual_pdfs(revue):
    path = revue.conf["Paths"]

    ## Create front pages for individual actors, if they don't already exist:
    # frontpages_list = []

    # for actor in revue.actors:
    #     file_name = "forside-{}.pdf".format(actor.name)
    #     if not os.path.isfile(os.path.join(path["pdf cache"], file_name)):
    #         tex = TeX(revue)
    #         tex.create_frontpage(subtitle=actor.name)
    #         frontpages_list.append([tex, file_name])

    # Det burde ordne sig selv nu:
    def tex_for_front_page( name ):
        tex = TeX( revue )
        tex.create_frontpage( subtitle = name )
        return tex
    
    frontpages_list = [ [ tex_for_front_page( actor.name ),
                          "forside-{}.pdf".format( actor.name )
                         ] for actor in revue.actors
                       ]

    # Create front pages:
    conv = cv.Converter()
    conv.parallel_textopdf(frontpages_list, outputdir=path["pdf cache"])

    total_list = []
    for actor in revue.actors:
        individual_list = (
            ( os.path.join( path["pdf cache"],
                            "forside-{}.pdf".format(actor.name)
                           ), "Forside" ),
            ( os.path.join( path["pdf"],"rolleliste.pdf" ), "Rolleliste", True ),
            ( os.path.join( path["pdf"],"aktoversigt.pdf" ), "Aktoversigt" )) +\
            ( tuple() if conf.getboolean("TeXing","skip thumbindex")\
              and not "thumbindex" in sys.argv
    	      else ( os.path.join(path["pdf"],"thumbindex.pdf"), "Registerindeks" ),) +\
    	    ( actor,
            ( os.path.join( path["pdf"],"kontaktliste.pdf"), "Kontaktliste" )
        )
        total_list.append((individual_list,
                           os.path.join(path["individual pdf"],
                                       "{}.pdf".format(actor.name))))

    pdf = PDF()
    pdf.parallel_pdfmerge(total_list)
    #pdf.pdfmerge(total_list)


def create_song_manus_pdf(revue):
    path = revue.conf["Paths"]

    # Create front page, if it doesn't already exist:
    # if not os.path.exists(os.path.join(path["pdf"], "cache")):
    #     os.mkdir(os.path.join(path["pdf"], "cache"))

    # if not os.path.isfile(os.path.join(path["pdf"], "cache", "forside-sangmanuskript.pdf")):
    # Det tager vare på sig selv nu
    tex = TeX(revue)
    tex.create_frontpage(subtitle="sangmanuskript")
    tex.topdf("forside-sangmanuskript.pdf", outputdir=os.path.join(path["pdf"], "cache"))

    # Create song manuscript:
    file_list = [os.path.join(path["pdf"],
                              "cache",
                              "forside-sangmanuskript.pdf")]
    if not revue.conf.getboolean("TeXing","skip thumbindex") \
       or "thumbindex" in sys.argv:
        file_list += [os.path.join(path["pdf"],
                                   "thumbindex.pdf"
                                   )
                      ]
    for act in revue.acts:
        for material in act.materials:
            if material.category == path["songs"]:
                file_list.append(
                    (
                        os.path.join(
                            path["pdf"],
                            os.path.dirname( os.path.relpath( material.path )),
                            "{}.pdf".format(material.file_name[:-4])
                        ),
                        material.title
                    )
                )

    pdf = PDF()
    pdf.pdfmerge(file_list, os.path.join(path["pdf"],"sangmanuskript.pdf"))

def roles_csv( revue ):
    mats = [ mat for act in revue.acts for mat in act.materials ]
    conv = cv.Converter()
    
    with Pool() as pool:
        counts = pool.map( conv.tex_to_wordcount, [ mat.path for mat in mats ] )

    for mat, count in zip( mats, counts ):
        mat.wordcounts = count
    
    try:
        fn = conf["Files"]["role overview"]
    except KeyError:
        revue.write_roles_csv()
        print( "Wrote roles.csv (default name, can be set in revytex.conf)" )
        return
    revue.write_roles_csv( fn )
    print( "Wrote {}".format( fn ))

def google_forms_signup( tex ):
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

    print( "" )
    for setting in settings:
        if setting not in role_settings:
            print("  {:<18} {}".format( setting.cmd + "=", setting.doc ) )
    sys.exit("\n")

actions = [
    Argument( "aktoversigt",
              "TeX en ny aktoversigt",
              lambda tex: ( tex.create_act_outline(),
                        tex.topdf("aktoversigt.pdf")
                        )
              ),

    Argument( "roles",
              "TeX en ny rolleliste",
              lambda tex: ( tex.create_role_overview(),
                            tex.topdf("rolleliste.pdf")
                           )
              ),

    Argument( "frontpage",
              "TeX en ny forside",
              lambda tex: ( tex.create_frontpage( ),
                            tex.topdf("forside.pdf")
                           )
              ),
    
    Argument( "thumbindex",
              "TeX et nyt registerindeks",
              lambda tex: ( tex.create_thumbindex(),
                            tex.topdf("thumbindex.pdf")
                            )
              ),

    Argument( "props",
              "Opdater rekvisitliste i Google Sheets (hvis det er sat op)",
              lambda tex: ( tex.create_props_list() )
              # TODO: måske hører den funktion ikke hjemme i tex længere?
              ),
              
    Argument( "contacts",
              "TeX en ny kontaktliste",
              lambda tex: ( tex.create_contacts_list("contacts.csv"),
                            tex.topdf("kontaktliste.pdf")
                           )
             ),
    
    Argument( "material",
              "Gen-TeX materialesiderne (hvis de er blevet ændret)",
              lambda tex: create_material_pdfs(revue)
              ),

    Argument( "individual",
              "Sammensæt nye individuelle manuskripter (hvis der er ændringer)",
              lambda tex: create_individual_pdfs(revue)
              ),

    Argument( "songmanus",
              "Sammensæt et nyt sangmanuskript (hvis der er ændringer)",
              lambda tex: create_song_manus_pdf(revue)
              ),

    Argument( "signup",
              "TeX en ny tilmeldingsblanket",
              lambda tex: ( tex.create_signup_form(),
                            tex.topdf("rolletilmelding.pdf")
                           )
              ),

    Argument( "roles-sheet",
              "Lav en csv(/tsv) fil med en oversigt over rollerne.",
              lambda tex: roles_csv( revue )
              ),

    Argument( "google-forms-signup",
              "Skriv roller og revydage ind i en Google Forms tilmeldingsformular.",
              google_forms_signup
             )
    ]

def create_parts(revue, args):
    tex = TeX(revue)

    if any( x in args for x in clobber_steps ):
        clobber_my_tex( revue, args )

    for action in actions:
        if action.cmd in args:
            action.action( tex )

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

            
def create( arguments = sys.argv ):

    # Load configuration file:
    conf.load("revytex.conf")
    conf.add_args([ x for x in arguments[1:] if x[0] != "-" ])
    
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
                    sys.exit(1)
    for flag in flags:
        if flag.cmd in \
           "".join( [ match[1] for match in
                      [ re.match( r"^-([^-]+)", arg ) for arg in arguments ]
                      if match ]
                     ):
            flag.action(conf) 

    if "plan" in arguments or not os.path.isfile("aktoversigt.plan"):
        sf.create_plan_file("aktoversigt.plan")
        sys.exit("Plan file 'aktoversigt.plan' created successfully.")

    global revue                # TODO: EVIL! :hiss:
    revue = cr.Revue.fromfile("aktoversigt.plan")
    path = revue.conf["Paths"]
    conv = cv.Converter()

    arglist = tuple( arguments[1:] )
    if all( arg[0] == "-" for arg in arglist ):
        arglist = default_commands
    elif "manus" in arguments:
        arglist = arglist + manus_commands

    try:
        create_parts( revue, arglist )
    except cv.ConversionError:
        print( "Some TeX files failed to compile. Can't create manuscripts.")
    else:

    	if "manus" in arguments:
    	    pdf = PDF()
    	    pdf.pdfmerge(
    	        (( os.path.join(path["pdf"],"forside.pdf"), "Forside" ),
    	         ( os.path.join(path["pdf"],"rolleliste.pdf"), "Rolleliste", True ),
    	         ( os.path.join(path["pdf"],"aktoversigt.pdf"), "Aktoversigt" )) +\
                ( tuple() if conf.getboolean("TeXing","skip thumbindex")\
                  and not "thumbindex" in arglist
    	          else ( os.path.join(path["pdf"],"thumbindex.pdf"), "Registerindeks" ),) +\
    	        ( revue,
    	         # ( os.path.join(path["pdf"],"rekvisitliste.pdf"), "Rekvisitliste" ),
    	         ( os.path.join(path["pdf"],"kontaktliste.pdf"), "Kontaktliste" )
    	         ),
    	        os.path.join(path["pdf"],"manuskript.pdf"))
    	
    	    print("Manuscript successfully created!")

if __name__ == "__main__":
    create()
