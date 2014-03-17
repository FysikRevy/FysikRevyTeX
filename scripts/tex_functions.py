import subprocess
import os
import tempfile
import shutil
import uuid
from time import localtime, strftime

def generate_pdf(pdfname, tex, repetitions=2):
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

    for i in range(repetitions):
        subprocess.call(["pdflatex", texfile])

    # proc=subprocess.Popen(['pdflatex','cover.tex'])
    # subprocess.Popen(['pdflatex',tex])
    # proc.communicate()

    os.rename(pdffile, pdfname)
    shutil.copy(pdfname, "{}/pdf".format(current_dir))
    os.chdir(current_dir)
    shutil.rmtree(temp)


def create_act_outline(revue):
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
    \t\t\\small{{Status: {status}, \\emph{{Tidsestimat: {length} minutter}}}}\n""".format(revue_name=m.revue, revue_year=m.year, status=m.status, length=m.length)
        
        tex += "\\end{enumerate}\n\n"

    tex += "\\end{document}"

    return tex


def create_role_overview(revue):
    
    # Find longest title for pretty printing:
    pad = max(len(m.title) for act in revue.acts for m in act.materials)
    pad += 2

    tex = r"""\documentclass[landscape,a3paper]{{article}}
\usepackage{{revy}}
\usepackage[danish]{{babel}}
\usepackage[utf8]{{inputenc}}
\usepackage{{graphicx}}
\usepackage[a3paper]{{geometry}} 

\frenchspacing

\title{{\large{{Rolleoversigt}}}}
\revyname{{{revue_name}}}
\revyyear{{{revue_year}}}
\version{{{current_time}}}

\textwidth 360mm
\textheight 260mm

\evensidemargin 0pt
\oddsidemargin 0pt

\headsep 1cm

\renewcommand{{\baselinestretch}}{{1.0}}
\newcommand{{\q}}{{\rule{{5.5mm}}{{0mm}}}}

\newcommand{{\actor}}[1]{{\rotatebox{{90}}{{#1\ }}}}
\def\makeatactive{{\catcode`\@=\active}}
\newcount\savedcat
{{\makeatactive\catcode`\|=\active\global\let|\ignorespaces
\gdef\actors{{\makeatactive\savedcat=\the\catcode`\|\catcode`\|=\active\@actors}}
\long\gdef\@actors#1{{#1@@\makeatother\catcode`\|=\savedcat}}
\gdef@#1@{{\def\tempa{{}}\def\tempb{{#1}}\ifx\tempa\tempb
\let\next\relax\else\def\next{{&\actor{{#1}}@}}\fi\next}}}}

\begin{{document}}
\begin{{center}}

\maketitle

\begin{{tabular}}{{|rl|*{{{N_actors}}}{{@{{}}c@{{}}|}}}}
\hline

&Sketch / Navn
""".format(current_time=strftime("%d-%m-%Y", localtime()), revue_name=revue.name, revue_year=revue.year, N_actors=len(revue.actors))

    
    tex += r"\actors{"
    for i in range(len(revue.actors)):
        # Print actor name left aligned:
        tex += "\n    {:<{width}}".format("", width=pad)
        for j in range(i):
            tex += "|   "
        tex += "@{}".format(revue.actors[i])
    tex += r"}\\\hline"

    for act in revue.acts:
        tex += r"\multicolumn{{{width}}}{{|l|}}{{\textbf{{{title}}}}}\\".format(width=len(revue.actors)+2, title=act.name)
        tex += "\n\\hline\n"

        for m, mat in enumerate(act.materials):
            tex += "\n{:2d} & {:<{width}}".format(m+1, mat.title, width=pad)
            for actor in revue.actors:
                for role in actor.roles:
                    if role.material == mat.title:
                        tex += "&{:>3}".format(role.abbreviation)
                        break
                else:
                    tex += r"& \q"
            tex += r"\\\hline"

    tex += """
\end{tabular}
\end{center}
\end{document}
"""

    return tex
