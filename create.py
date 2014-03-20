import os
import sys
sys.path.append("scripts/")

import classy_revy as cr
import tex_functions as tex
import helper_functions as hf

def create_material_pdfs(revue):
    file_list = []
    for act in revue.acts:
        for material in act.materials:
            #if material.category in ["sange", "sketches"]:
            file_list.append(material.path)

    hf.generate_multiple_pdfs(file_list)
    return 0


if __name__ == "__main__":

    revue = cr.Revue.fromfile("aktoversigt.plan")

    if len(sys.argv) < 2 or "manus" in sys.argv:
        # Create everything.
        
        # Front page
        hf.generate_pdf_from_file("templates/frontpage.tex")
        os.replace("templates/frontpage.pdf", "pdf/frontpage.pdf")

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
            
        hf.merge_pdfs(["pdf/frontpage.pdf", 
                       "pdf/aktoversigt.pdf", 
                       "pdf/rolleliste.pdf", 
                       revue, 
                       "pdf/rekvisitliste.pdf"], 
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
            hf.generate_pdf_from_file("templates/frontpage.tex")
            os.replace("templates/frontpage.pdf", "pdf/frontpage.pdf")
        
        if "props" in sys.argv:
            props = tex.create_props_list(revue)
            hf.generate_pdf("rekvisitliste.pdf", props)
