from time import localtime, strftime

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
                    if role.material.title == mat.title:
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


def create_props_list(revue):

    tex = r"""\documentclass[a4paper,11pt,oneside]{article}
\usepackage[left=0cm,top=0cm,right=0cm,nohead,nofoot]{geometry}
\usepackage{a4wide}
\usepackage{tabularx}
\usepackage{charter,euler}
\usepackage[danish]{babel,varioref}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\frenchspacing
\usepackage{longtable}
\newcommand{\mtitle}[1]{\hline \multicolumn{3}{|l|}{\textbf{#1}} \\ \hline}
\title{Rekvisitliste}
\pagenumbering{arabic}

\textwidth 190mm
\textheight 270mm
\evensidemargin 0pt
\oddsidemargin -15mm
\topmargin -2cm
\headsep 0.5cm

\begin{document}

\maketitle

\setlength\LTleft{0pt}
\setlength\LTright{0pt}
"""

    for act in revue.acts:
        tex += r"""

\begin{{longtable}}{{|p{{7cm}}|p{{4cm}}|p{{7cm}}|}}
\hline
\textbf{{{act_title}}} & Ansvarlig & Status \\
\endfirsthead

\hline
\textbf{{{act_title} (fortsat)}} & Ansvarlig & Status  \\
\endhead

\hline \endfoot
""".format(act_title=act.name)
    
        for m in act.materials:
            tex += "\n\\mtitle{{{m_title}}}\n".format(m_title = m.title)
            for prop in m.props:
                tex += r"\textbf{{{prop}}} & {responsible} & \\ {description} & & \\ \hline".format(prop=prop.prop, responsible=prop.responsible, description=prop.description)
                tex += "\n"

        tex += "\\end{longtable}\n\n"
    
    tex += "\\end{document}\n\n"

    return tex


def create_frontpage(revue, config):
    c = config["Frontpage"]
    tex = r"""
\documentclass[11pt]{{article}}
\usepackage[danish]{{babel}}
\usepackage[utf8]{{inputenc}}
\usepackage{{vmargin}}
\setpapersize{{A4}}
\setmarginsrb{{20mm}}{{15mm}}{{20mm}}{{20mm}}{{12pt}}{{11mm}}{{0pt}}{{11mm}}
\usepackage[T1]{{fontenc}}                 % æøåÆØÅ
\usepackage{{amsmath}}                     % Matematiske kommandoer
\usepackage{{amssymb}}                     % Matematiske symboler


%-----------------------------------------------------%
%                   KOMMANDOER                        %
%-----------------------------------------------------%
\newcommand{{\FysikRevy}}{{$\textrm{{\textsf{{FysikRevy}}}}^{{\textrm{{\textsf{{\tiny{{TM}}}}}}}}$}}
\newcommand{{\Kairsten}}{{K$\frac{{a}}{{i}}$rsten}}
\newcommand{{\Simon}}{{$\psi$-mon}}
\newcommand{{\p}}{{$\Psi$}}

\addtolength{{\topmargin}}{{-10pt}}
\addtolength{{\textheight}}{{20pt}}

\newfont{{\cmfnt}}{{ecssdc10.pk at 50pt}}
\newfont{{\cmfntt}}{{ecssdc10.pk at 30pt}}
\newfont{{\cmfnttt}}{{ecssdc10.pk at 20pt}}
\newfont{{\frfont}}{{eclq8.pk at 80pt}}
\newfont{{\frfontii}}{{eclq8.pk at 30pt}}

\parindent=0pt
\parskip=5pt

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%			Start dokument		%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\begin{{document}}
\thispagestyle{{empty}}

\begin{{flushright}}
	{{\tiny {top_quote}}}
\end{{flushright}}
\hrule
\begin{{center}}
{{\frfont $\textrm{{\frfont{{FysikRevy}}}}^{{\textrm{{\frfontii{{{{TM}}}}}}}}$}}
\\ --- {{\frfontii tekster}} ---
\vspace{{2cm}}

{{\cmfntt{{Ver. {version}}}}}\\ %\Huge{{\textbf{{$|5+i\sqrt{{11}}|$}}}}}}}}\\
\vspace{{5mm}}
{{\cmfnttt{{\today}}}}\\
\vspace{{1cm}}
\end{{center}}


\begin{{center}}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% INDLEDENDE MORALPRÆDIKEN
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\Large
Du holder nu i hånden de guddommelige \TeX ster til {name} {year}. Dette indebærer (som tidligere år) følgende:
\begin{{itemize}}
\item Du (\TeX)hæfter for disse \TeX ster med dit liv.
\item Hvis du mister dem vil du blive chapset i osten med et vådt hestebrød!
\item Hvis du viser dem til ikke-indviede er dit liv ødelagt, og du kan lige så 
godt lade dig indskrive på datalogi og tage menneske-datamaskine interaktion.
\item Hvis du gerne vil undgå, at andre tager dit \TeX hæfte som gidsel,
skal du skrive dit navn på forsiden. Så er du sikker på at andre ikke vil kunne
finde på at stjæle DIT \TeX hæfte. 
\item Hvis du ikke skriver navn på dit \TeX hæfte, må du først gå hjem, når du har fået eduroam til at fungere.
\end{{itemize}}
\end{{center}}
\vfill
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% FORSIDEBILLEDE
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%\begin{{center}}
%\epsfig{{file=60meterhest.eps,width=5cm}}\\
%\end{{center}}

\vfill
Årets \TeX hæfte er sat i \LaTeXe.
\begin{{center}}
	{{\tiny {bottom_quote}}}
\end{{center}}
\end{{document}}""".format(version = c["version"],
                           top_quote = c["top quote"],
                           bottom_quote = c["bottom quote"],
                           name=revue.name, 
                           year=revue.year)

    return tex


def create_contacts_list(fname):
    """Parses a CSV file to create the contacts list. Comments starting with # will be interpreted as section headings. 
Comments starting with ## will be interpreted as column headers in the list."""

    tex = r"""
\documentclass[a4paper,9pt,oneside]{article}
%\usepackage[left=0cm,top=1cm,right=0cm,nohead,nofoot]{geometry}
\usepackage[a4paper,hmargin=2.5cm,nohead,nofoot]{geometry}
\usepackage{charter,euler}
\usepackage[danish]{babel,varioref}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{longtable}
\usepackage{booktabs}
\begin{document}
"""
    
    first_table = True

    with open(fname, 'r') as f:
        for line in f.readlines():
            line = line.strip()

            if len(line) > 0:
                if line[0] == '#' and line[1] != '#':
                    # Line is a heading.

                    # We should end the previous table, if any:
                    if not first_table:
                        tex += "\n\\end{longtable}\\vspace*{1em}\n"

                    tex += "{{\Large\\bfseries {heading}}}\n".format(heading=line.strip("# "))

                elif line[0] == '#' and line[1] == '#':
                    # Line specifies column headers.
                    first_table = False

                    split_line = line.strip('# ').split(';')
                    n_cols = len(split_line)
                    
                    tex += "\\begin{{longtable}}{{*{{{n}}}{{l}}}}\n".format(n=n_cols)

                    headers = ""
                    for i,word in enumerate(split_line):
                        if i == 0:
                            headers += "\\textbf{{{word}}}".format(word=word.strip())
                        else:
                            headers += " & \\textbf{{{word}}}".format(word=word.strip())
                    headers += "\\\\\n"
                    tex += r"""
\toprule
{headers}
\midrule
\endfirsthead

\toprule
{headers}
\midrule
\endhead

\bottomrule
\endfoot
""".format(headers=headers)

                else:
                    # Line contains contact information:
                    split_line = line.strip().split(';')
                    if len(split_line) != n_cols:
                        print("Warning! Line does not have the right number of columns! Line: {}".format(line))

                    for i,word in enumerate(split_line):
                        if i == 0:
                            tex += "{word}".format(word=word.strip())
                        else:
                            tex += " & {word}".format(word=word.strip())

                    tex += "\\\\\n"

    tex += "\\end{longtable}\n\\end{document}"

    return tex

