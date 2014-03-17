import sys
sys.path.append("scripts/")

import classy_revy as cr
import tex_functions as tex


revue = cr.Revue.fromfile("aktoversigt.plan")

if len(sys.argv) < 2:
    # Create everything.
    aktoversigt = tex.create_act_outline(revue)
    tex.generate_pdf("aktoversigt.pdf", aktoversigt)

elif "aktoversigt" in sys.argv:
    aktoversigt = tex.create_act_outline(revue)
    tex.generate_pdf("aktoversigt.pdf", aktoversigt)
