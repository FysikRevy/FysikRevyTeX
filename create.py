import sys
sys.path.append("scripts/")

import classy_revy as cr
import tex_functions as tex


revue = cr.Revue.fromfile("aktoversigt.plan")

if len(sys.argv) < 2:
    # Create everything.
    aktoversigt = tex.create_act_outline(revue)
    tex.generate_pdf("aktoversigt.pdf", aktoversigt)
    
    roles = tex.create_role_overview(revue)
    tex.generate_pdf("rolleliste.pdf", roles)

else:
    if "aktoversigt" in sys.argv:
        aktoversigt = tex.create_act_outline(revue)
        tex.generate_pdf("aktoversigt.pdf", aktoversigt)

    if "roles" in sys.argv:
        roles = tex.create_role_overview(revue)
        tex.generate_pdf("rolleliste.pdf", roles)
