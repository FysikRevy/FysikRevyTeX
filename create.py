#!/usr/bin/env python3
from configparser import ConfigParser
import os
import sys
sys.path.append("scripts/")

import classy_revy as cr
import tex_functions as tex
import helper_functions as hf
import setup_functions as sf
           

def create_material_pdfs(revue):
    file_list = []
    for act in revue.acts:
        for material in act.materials:
            #if material.category in ["sange", "sketches"]:
            file_list.append(material.path)

    hf.generate_multiple_pdfs(file_list)

def create_individual_pdfs(revue):
    # TODO: Make this run in parallel for all actors.
    for actor in revue.actors:
        file_list = ["pdf/frontpage.pdf", 
                     "pdf/aktoversigt.pdf", 
                     "pdf/rolleliste.pdf",
                     actor,
                     "pdf/rekvisitliste.pdf"]
        hf.merge_pdfs(file_list, "pdf/individuals/{}.pdf".format(actor.name))

def create_song_manus_pdf(revue):
    file_list = []
    for act in revue.acts:
        for material in act.materials:
            if material.category == "sange":
                file_list.append("{}.pdf".format(material.path[-4:]))
    hf.merge_pdfs(file_list, "pdf/sangmanuskript.pdf")



if __name__ == "__main__":

    if "plan" in sys.argv or not os.path.isfile("aktoversigt.plan"):
        sf.create_plan_file("aktoversigt.plan")
        sys.exit("Plan file 'aktoversigt.plan' created successfully.")
            

    revue = cr.Revue.fromfile("aktoversigt.plan")
    conf = ConfigParser()
    conf.read("revytex.conf")

    if len(sys.argv) < 2 or "manus" in sys.argv:
        # Create everything.
        
        # Front page
        frontpage = tex.create_frontpage(revue, config=conf)
        hf.generate_pdf("frontpage.pdf", frontpage)

        # Aktoversigt:
        aktoversigt = tex.create_act_outline(revue)
        hf.generate_pdf("aktoversigt.pdf", aktoversigt)
        
        # Role overview:
        roles = tex.create_role_overview(revue)
        hf.generate_pdf("rolleliste.pdf", roles)
        
        # Props list:
        props = tex.create_props_list(revue)
        hf.generate_pdf("rekvisitliste.pdf", props)
        
        # PDFs for sketches/songs:
        create_material_pdfs(revue)
        
        # Contacts list:
        contacts = tex.create_contacts_list("templates/contacts.csv")
        hf.generate_pdf("kontaktliste.pdf", contacts)
            
        hf.merge_pdfs(["pdf/frontpage.pdf", 
                       "pdf/aktoversigt.pdf", 
                       "pdf/rolleliste.pdf", 
                       revue, 
                       "pdf/rekvisitliste.pdf", 
                       "pdf/kontaktliste.pdf"], 
                       "pdf/manuskript.pdf")

        print("Manuscript created successfully!")

    else:
        if "aktoversigt" in sys.argv:
            aktoversigt = tex.create_act_outline(revue)
            hf.generate_pdf("aktoversigt.pdf", aktoversigt)

        if "roles" in sys.argv:
            roles = tex.create_role_overview(revue)
            hf.generate_pdf("rolleliste.pdf", roles)

        if "material" in sys.argv:
            create_material_pdfs(revue)

        if "frontpage" in sys.argv:
            frontpage = tex.create_frontpage(revue, config=conf)
            hf.generate_pdf("frontpage.pdf", frontpage)
        
        if "props" in sys.argv:
            props = tex.create_props_list(revue)
            hf.generate_pdf("rekvisitliste.pdf", props)

        if "individual" in sys.argv:
            create_individual_pdfs(revue)

        if "contacts" in sys.argv:
            contacts = tex.create_contacts_list("templates/contacts.csv")
            hf.generate_pdf("kontaktliste.pdf", contacts)

        if "songmanus" in sys.argv:
            create_song_manus_pdf(revue)
