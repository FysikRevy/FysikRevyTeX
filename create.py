#!/usr/bin/env python3
from configparser import ConfigParser
import os
import sys
sys.path.append("scripts")

import classy_revy as cr
import setup_functions as sf
import converters as cv
import tex 
import pdf 
           

def create_material_pdfs(revue):
    file_list = []
    for act in revue.acts:
        for material in act.materials:
            file_list.append(material.path)

    conv = Converter(revue.conf)
    conv.parallel_textopdf(file_list)

def create_individual_pdfs(revue):
    path = revue.config["Paths"]
    total_list = []
    for actor in revue.actors:
        individual_list = (os.path.join(path["pdf"],"frontpage.pdf"), 
                             os.path.join(path["pdf"],"aktoversigt.pdf"), 
                             os.path.join(path["pdf"],"rolleliste.pdf"),
                             actor,
                             os.path.join(path["pdf"],"rekvisitliste.pdf"))
        total_list.append((individual_list, 
                           os.path.join(path["individual pdf"],
                                       "{}.pdf".format(actor.name))))

    pdf = PDF(revue.conf)
    pdf.parallel_pdfmerge(total_list)

def create_song_manus_pdf(revue):
    path = revue.config["Paths"]
    file_list = [os.path.join(path["pdf"],"frontpage.pdf")]
    for act in revue.acts:
        for material in act.materials:
            if material.category == "sange":
                file_list.append("{}.pdf".format(material.path[:-4]))
    
    pdf = PDF(revue.conf)
    pdf.pdfmerge(file_list, os.path.join(path["pdf"],"sangmanuskript.pdf"))


def create_parts(revue, args):
    tex = TeX(revue)

    if "aktoversigt" in sys.argv:
        tex.create_act_outline()
        tex.topdf("aktoversigt.pdf")

    elif "roles" in sys.argv:
        tex.create_role_overview()
        tex.topdf("rolleliste.pdf")

    elif "material" in sys.argv:
        create_material_pdfs(revue)

    elif "frontpage" in sys.argv:
        tex.create_frontpage()
        tex.topdf("forside.pdf")
    
    elif "props" in sys.argv:
        tex.create_props_list()
        tex.topdf("rekvisitliste.pdf")

    elif "individual" in sys.argv:
        create_individual_pdfs(revue)

    elif "contacts" in sys.argv:
        tex.create_contacts_list("contacts.csv")
        tex.topdf("kontaktliste.pdf")

    elif "songmanus" in sys.argv:
        create_song_manus_pdf(revue)
    
    elif "signup" in sys.argv:
        tex.create_signup_form()
        tex.topdf("rolletilmelding.pdf")



if __name__ == "__main__":

    if "plan" in sys.argv or not os.path.isfile("aktoversigt.plan"):
        sf.create_plan_file("aktoversigt.plan")
        sys.exit("Plan file 'aktoversigt.plan' created successfully.")

    revue = cr.Revue.fromfile("aktoversigt.plan")
    path = revue.config["Paths"]
    conv = cv.Converter(revue.conf)

    if len(sys.argv) < 2 or "manus" in sys.argv:
        arglist = ("material", "aktoversigt", "roles", "frontpage", "props",
                   "contacts", "individual", "songmanus")
    else:
        arglist = sys.argv[1:]

    for arg in arglist:
        create_parts(revue, arg)


    if len(sys.argv) < 2 or "manus" in sys.argv:
        pdf = PDF(revue.conf)
        pdf.pdfmerge((os.path.join(path["pdf"],"forside.pdf"), 
                      os.path.join(path["pdf"],"aktoversigt.pdf"), 
                      os.path.join(path["pdf"],"rolleliste.pdf"), 
                      revue, 
                      os.path.join(path["pdf"],"rekvisitliste.pdf"), 
                      os.path.join(path["pdf"],"kontaktliste.pdf")), 
                      os.path.join(path["pdf"],"manuskript.pdf"))

        print("Manuscript successfully created!")
