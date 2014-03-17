import subprocess
import os
import tempfile
import shutil
import uuid
from time import localtime, strftime

def generate_pdf(pdfname, tex):
    "Generates a pdf from a TeX string."

    current_dir = os.getcwd()
    temp = tempfile.mkdtemp()
    os.chdir(temp)
    os.symlink("{}/revy.sty".format(current_dir), "revy.sty")

    #tempname = "{}{}".format(uuid.uuid4(), ".tex") 
    tempname = uuid.uuid4() 
    texfile = "{}.tex".format(tempname)
    pdffile = "{}.pdf".format(tempname)

    with open(texfile,'w') as f:
        f.write(tex)

    subprocess.call(["ls","-la"])

    subprocess.call(["pdflatex", texfile])
    subprocess.call(["pdflatex", texfile])

    # proc=subprocess.Popen(['pdflatex','cover.tex'])
    # subprocess.Popen(['pdflatex',tex])
    # proc.communicate()

    os.rename(pdffile, pdfname)
    shutil.copy(pdfname, "{}/pdf".format(current_dir))
    shutil.rmtree(temp)

def create_act_outline(revue):
#\pdfminorversion=4
    tex = r"""\documentclass[danish]{{article}}
\usepackage{{revy}}
\usepackage{{babel}}
\usepackage[utf8]{{inputenc}}
\usepackage{{anysize}}

\title{{Aktoversigt}}

\version{{{current_time}}}
\revyname{{{revue_name}}}
\revyyear{{{revue_year}}}

\begin{{document}}

\maketitle

""".format(current_time=strftime("%d-%m-%Y", localtime()), revue_name=revue.name, revue_year=revue.year)

    for act in revue.acts:
        tex += "\\section*{{{act_title} \\small{{\\textbf{{\\emph{{(Tidsestimat: {act_length} minutter)}}}}}}}}\n".format(act_title=act.name, act_length=act.get_length())
        tex += "\\begin{enumerate}\n"

        for m in act.materials:
            tex += "\t\\item \\textbf{{{title}}} ".format(title = m.title)

            if m.melody:
                tex += "({melody}) ".format(melody=m.melody)

            tex += """\\emph{{{revue_name} {revue_year}}}\\\\
    \t\t\\small{{Status: {status}, \\emph{{Tidsestimat: {length} minutter}}}}\n""".format(revue_name=m.revy, revue_year=m.year, status=m.status, length=m.length)
        
        tex += "\\end{enumerate}\n\n"

    tex += "\\end{document}"

    return tex

