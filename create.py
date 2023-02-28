#!/usr/bin/env python3
import glob
import os
import sys
sys.path.append("scripts")

import classy_revy as cr
import setup_functions as sf
import converters as cv
import config as cf
from tex import TeX
from clobberers import clobber_steps, clobber_my_tex
from pdf import PDF

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
            ( os.path.join( path["pdf"],"aktoversigt.pdf" ), "Aktoversigt" ),
            ( os.path.join( path["pdf"],"rolleliste.pdf" ), "Rolleliste" ),
            actor,
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
    file_list = [os.path.join(path["pdf"], "cache", "forside-sangmanuskript.pdf")]
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


def create_parts(revue, args):
    tex = TeX(revue)

    if any( x in args for x in clobber_steps ):
        clobber_my_tex( revue, args )

    if "aktoversigt" in args:
        tex.create_act_outline()
        tex.topdf("aktoversigt.pdf")

    if "roles" in args:
        tex.create_role_overview()
        tex.topdf("rolleliste.pdf")

    if "frontpage" in args:
        tex.create_frontpage( )
        tex.topdf("forside.pdf")

    if "props" in args:
        tex.create_props_list()
        tex.topdf("rekvisitliste.pdf")

    if "contacts" in args:
        tex.create_contacts_list("contacts.csv")
        tex.topdf("kontaktliste.pdf")

    if "material" in args:
        create_material_pdfs(revue)

    if "individual" in args:
        create_individual_pdfs(revue)

    if "songmanus" in args:
        create_song_manus_pdf(revue)

    if "signup" in args:
        tex.create_signup_form()
        tex.topdf("rolletilmelding.pdf")

if __name__ == "__main__":

    if "plan" in sys.argv or not os.path.isfile("aktoversigt.plan"):
        sf.create_plan_file("aktoversigt.plan")
        sys.exit("Plan file 'aktoversigt.plan' created successfully.")

    # Load configuration file:
    conf.load("revytex.conf")
    conf.add_args([ x for x in sys.argv if x[0] != "-" ])
    if "--tex-all" in sys.argv:
        conf["TeXing"]["force TeXing of all files"] = "yes"
    if "-v" in sys.argv:
        conf["TeXing"]["verbose output"] = "yes"

    revue = cr.Revue.fromfile("aktoversigt.plan")
    path = revue.conf["Paths"]
    conv = cv.Converter()

    if len(conf.cmd_parts) == 0:
        arglist = ("aktoversigt", "roles", "frontpage", "props",
                   "contacts", "material","individual", "songmanus")
    elif "manus" in sys.argv:
        arglist = ("aktoversigt", "roles", "frontpage", "props",
                   "contacts", "material")
    else:
        arglist = sys.argv[1:]

    try:
        create_parts( revue, arglist )
    except cv.ConversionError:
        print( "Some TeX files failed to compile. Can't create manuscripts.")
    else:

    	if len(conf.cmd_parts) == 0 or "manus" in sys.argv:
    	    pdf = PDF()
    	    pdf.pdfmerge(
    	        (( os.path.join(path["pdf"],"forside.pdf"), "Forside" ),
    	         ( os.path.join(path["pdf"],"aktoversigt.pdf"), "Aktoversigt" ),
    	         ( os.path.join(path["pdf"],"rolleliste.pdf"), "Rolleliste" ),
    	         revue,
    	         ( os.path.join(path["pdf"],"rekvisitliste.pdf"), "Rekvisitliste" ),
    	         ( os.path.join(path["pdf"],"kontaktliste.pdf"), "Kontaktliste" )
    	         ),
    	        os.path.join(path["pdf"],"manuskript.pdf"))
    	
    	    print("Manuscript successfully created!")
