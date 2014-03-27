import re
import sys

from base_classes import Prop, Role

# Regular expression that extracts everything between \ and {:
cmd_re = re.compile(r"^.*\\(.*){.*$")

# Regular expression that extracts everything between { and }:
kw_re = re.compile(r"^.*{(.*)}.*$")

# Regular expression that extracts everything between [ and ]:
opt_re = re.compile(r"^.*\[(.*)\].*$")

# Regular expression that extracts everything ] and to the end of the line:
eol_re = re.compile(r"^.*\](.*).*$")


def extract_multiple_lines(lines, line_number, start_delimiter='{', end_delimiter='}'):
    "Extract the whole string of a command that spans multiple lines (e.g. \scene)."

    line = lines[line_number]
    
    # Find index of start delimiter and instantiate the end index:
    start_index = line.find(start_delimiter)
    end_index = 0
    
    # Get the start of the string, we want to return:
    string = line[start_index+1:].strip() # strip spaces and newlines

    # Set counters on the number of start and end delimiters (in case there should be a
    # sub-command like \emph{} within the string, we want to find:
    n_start = line.count(start_delimiter)
    n_end = line.count(end_delimiter)

    line_n = line_number

    while n_start > n_end:
        line_n += 1
        line = lines[line_n]

        for i,c in enumerate(line):
            # Count the number of start and end delimiters, and note the index of any
            # end delimiter:
            if c == start_delimiter:
                n_start += 1
            elif c == end_delimiter:
                n_end += 1
                end_index = i

            if n_start == n_end:
                break

    for l in range(line_number+1, line_n):
        # Strip spaces and newlines, but add a space between the new and past line:
        string += " " + lines[l].strip() 

    # Add the ending:
    string += lines[line_n][:end_index]

    return string.strip()


class TeX:
    def __init__(self, revue):
        self.revue = revue
        self.conf = self.revue.conf

        self.tex = ""
        
        # Create dictionary to store relevant information:
        self.info = {}


    def read(self, fname, encoding='utf-8'):
        "Read a TeX file without parsing it."
        with open(fname, 'r', encoding=encoding) as f:
            self.tex = f.read()


    def write(self, fname, encoding='utf-8'):
        "Write to a TeX file."
        with open(fname, 'w', encoding=encoding) as f:
            f.write(self.tex)


    def parse(self, fname, encoding='utf-8'):
        "Parse a TeX file and extract revue relevant information to a dictionary."
        
        # Create lists for other stuff:
        self.info["props"] = []
        self.info["roles"] = []
        self.info["appearing_roles"] = set() # How many people/abbreviations that occur in the actual sketch/song.

        # List of keywords/commands to ignore, i.e. that are not relevant to extract:
        ignore_list = ["documentclass", "usepackage", "begin", "end", "maketitle", "act", "scene"]

        # List of important keywords/commands:
        important_list = ["prop", "role", "sings", "says"]

        with open(filename, mode='r', encoding=encoding) as f:
            lines = f.readlines()
            for n,line in enumerate(lines):
                line = line.strip() # Remove leading and trailing whitespaces
                if len(line) > 0 and line[0] == '\\': # only look for a command

                    if "{" not in line:
                        # If it is a strange line, extract the first part (everything until the
                        # first non-alphanumeric character that isn't '\':
                        first_part = re.findall("\w+", line)[0]

                        if first_part not in ignore_list:
                            # Find also the second part, i.e. whatever follows the first part (including
                            # the non-alphanumeric character):
                            end_part = re.findall("^.\w+(.*)", line)[0]

                            # Store the info:
                            self.info[first_part] = end_part

                    else:
                        command = re.findall("\w+", line)[0] # Extract (the first) command using regex

                        if command not in ignore_list:

                            try:
                                keyword = kw_re.findall(line)[0] # Extract (the first) keyword using regex
                            except IndexError:
                                # There is no ending '}' in the line.
                                keyword = extract_multiple_lines(lines, n)
                            
                            # Now check whether the command is one of the important ones:
                            if command in important_list:
                                if command == "prop":
                                    prop = keyword

                                    try:
                                        responsible = opt_re.findall(line)[0]
                                        index = line.rfind("]")
                                    except IndexError:
                                        # There is no responsible for this item.
                                        responsible = ""
                                        index = line.rfind("}")

                                    description = line[index+1:].strip()
                                    self.info["props"].append(Prop(prop, responsible, description))

                                elif command == "role":
                                    abbreviation = keyword
                                    name = opt_re.findall(line)[0]
                                    role = eol_re.findall(line)[0]
                                    if len(name) > 0:
                                        # Only store the role if it is not empty:
                                        self.info["roles"].append(Role(abbreviation, name, role))

                                elif command in ("sings", "says"):
                                    # We count how many abbreviations actually appear in the sketch/song
                                    # in order to find missing persons in the roles list.
                                    abbreviation = keyword
                                    self.info["appearing_roles"].add(abbreviation)
                            else:
                                # Store information:
                                self.info[command] = keyword


    def topdf(self, pdfname, repetitions=2, encoding='utf-8'):
        "Convert internally stored TeX code to PDF using pdflatex."
        converter = Converter(self.conf)
        converter.textopdf(self.tex, pdfname, repetitions, encoding)


    #----------------------------------------------------------------------

    def create_act_outline(self, templatefile='templates/act_outline_template.tex', encoding='utf-8'):
        "Create act outline from Revue object."
        
        self.tex = ""

        with open(templatefile, 'r', encoding=encoding) as f:
            template = f.read().split("<+ACTOUTLINE+>")

        template[0] = template[0].replace("<+VERSION+>", strftime("%d-%m-%Y", localtime()))
        template[0] = template[0].replace("<+REVUENAME+>", self.name)
        template[0] = template[0].replace("<+REVUEYEAR+>", self.year)

        for act in self.revue.acts:
            self.tex += "\\section*{{{act_title} \\small{{\\textbf{{\\emph{{(Tidsestimat: {act_length} minutter)}}}}}}}}\n".format(act_title=act.name, act_length=act.get_length())
            self.tex += "\\begin{enumerate}\n"

            for m in act.materials:
                self.tex += "\t\\item \\textbf{{{title}}} ".format(title = m.title)

                if m.melody:
                    self.tex += "({melody}) ".format(melody=m.melody)

                self.tex += """\\emph{{{revue_name} {revue_year}}}\\\\
        \t\t\\small{{Status: {status}, \\emph{{Tidsestimat: {length} minutter}}}}\n""".format(revue_name=m.revue, revue_year=m.year, status=m.status, length=m.length)
            
            self.tex += "\\end{enumerate}\n\n"


        self.tex = "\n".join(template.insert(1,self.tex))


    #----------------------------------------------------------------------

    def create_role_overview(self, templatefile='templates/role_overview_template.tex', encoding='utf-8'):

        self.tex = ""

        with open(templatefile, 'r', encoding=encoding) as f:
            template = f.read().split("<+ROLEMATRIX+>")

        template[0] = template[0].replace("<+VERSION+>", strftime("%d-%m-%Y", localtime()))
        template[0] = template[0].replace("<+REVUENAME+>", self.revue.name)
        template[0] = template[0].replace("<+REVUEYEAR+>", self.revue.year)
        template[0] = template[0].replace("<+NACTORS+>", len(self.revue.actors))

        # Find longest title for pretty printing:
        pad = max(len(m.title) for act in self.revue.acts for m in act.materials)
        pad += 2

        self.tex += r"\actors{"
        for i in range(len(self.revue.actors)):
            # Print actor name left aligned:
            self.tex += "\n    {:<{width}}".format("", width=pad)
            for j in range(i):
                self.tex += "|   "
            self.tex += "@{}".format(self.revue.actors[i])
        self.tex += r"}\\\hline"

        for act in self.revue.acts:
            self.tex += r"\multicolumn{{{width}}}{{|l|}}{{\textbf{{{title}}}}}\\".format(width=len(self.revue.actors)+2, title=act.name)
            self.tex += "\n\\hline\n"

            for m, mat in enumerate(act.materials):
                self.tex += "\n{:2d} & {:<{width}}".format(m+1, mat.title, width=pad)
                for actor in self.revue.actors:
                    for role in actor.roles:
                        if role.material.title == mat.title:
                            self.tex += "&{:>3}".format(role.abbreviation)
                            break
                    else:
                        self.tex += r"& \q"
                self.tex += r"\\\hline"
        
        self.tex = "\n".join(template.insert(1,self.tex))



    #----------------------------------------------------------------------

    def create_props_list(self, templatefile='templates/props_list_template.tex', encoding='utf-8'):

        self.tex = ""

        with open(templatefile, 'r', encoding=encoding) as f:
            template = f.read().split("<+PROPSLIST+>")

        for act in self.revue.acts:
            self.tex += r"""
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
                self.tex += "\n\\mtitle{{{m_title}}}\n".format(m_title = m.title)
                for prop in m.props:
                    self.tex += r"\textbf{{{prop}}} & {responsible} & \\ {description} & & \\ \hline".format(prop=prop.prop, responsible=prop.responsible, description=prop.description)
                    self.tex += "\n"

            self.tex += "\\end{longtable}\n\n"

        self.tex = "\n".join(template.insert(1,self.tex))



    #----------------------------------------------------------------------

    def create_frontpage(self, templatefile='templates/frontpage_template.tex', encoding='utf-8'):

        self.tex = ""

        with open(templatefile, 'r', encoding=encoding) as f:
            template = f.read()

        self.tex = template.replace("<+VERSION+>", self.revue.conf["Frontpage"]["version"])

        if self.revue.conf["Revue info"]["revue name"] == "\\FysikRevy\\texttrademark":
            self.tex = self.tex.replace("<+REVUENAME+>", "\\FysikRevy")
        else:
            self.tex = self.tex.replace("<+REVUENAME+>", self.revue.name)

        self.tex = self.tex.replace("<+REVUEYEAR+>", self.revue.year)
        self.tex = self.tex.replace("<+TOPQUOTE+>", self.revue.conf["Frontpage"]["top quote"])
        self.tex = self.tex.replace("<+BOTTOMQUOTE+>", self.revue.conf["Frontpage"]["bottom quote"])


    #----------------------------------------------------------------------

    def create_signup_form(self, templatefile='templates/signup_form_template.tex', encoding='utf-8'):

        self.tex = ""

        with open(templatefile, 'r', encoding=encoding) as f:
            template = f.read().split("<+SIGNUPFORM+>")

        for act in self.revue.acts:
            self.tex += "\n\n\\begin{longtable}{|p{7cm}|cccl|}\n"

            self.tex += "\\hline\n"
            self.tex += r"\textbf{{{title}}} & ++ & + & - & Kommentar \\".format(title = act.name)
            self.tex += "\n\\endfirsthead\n\n"

            self.tex += "\\hline\\endfoot\n"

            for material in act.materials:
                self.tex += "\n\\mtitle{{{title}}}\n".format(title=material.title)

                for role in material.roles:
                    if role.role == "":
                        self.tex += "\\role{{{title}}}\n".format(title=role.abbreviation)
                    else:
                        self.tex += "\\role{{{title}}}\n".format(title=role.role)

            self.tex += "\\end{longtable}\n\n"



        
        self.tex = "\n".join(template.insert(1,self.tex))


    #----------------------------------------------------------------------

    def create_contacts_list(self, contactsfile, templatefile='templates/contacts_list_template.tex', encoding='utf-8'):
        """Parses a CSV file to create the contacts list. Comments starting with # will be interpreted as section headings. 
    Comments starting with ## will be interpreted as column headers in the list."""

        self.tex = ""

        with open(templatefile, 'r', encoding=encoding) as f:
            template = f.read().split("<+CONTACTS+>")


        first_table = True

        with open(contactsfile, 'r', encoding=encoding) as c:
            lines = c.readlines()

        for line in lines:
            line = line.strip()

            if len(line) > 0:
                if line[0] == '#' and line[1] != '#':
                    # Line is a heading.

                    # We should end the previous table, if any:
                    if not first_table:
                        self.tex += "\n\\end{longtable}\\vspace*{1em}\n"

                    self.tex += "{{\Large\\bfseries {heading}}}\n".format(heading=line.strip("# "))

                elif line[0] == '#' and line[1] == '#':
                    # Line specifies column headers.
                    first_table = False

                    split_line = line.strip('# ').split(';')
                    n_cols = len(split_line)
                    
                    self.tex += "\\begin{{longtable}}{{*{{{n}}}{{l}}}}\n".format(n=n_cols)

                    headers = ""
                    for i,word in enumerate(split_line):
                        if i == 0:
                            headers += "\\textbf{{{word}}}".format(word=word.strip())
                        else:
                            headers += " & \\textbf{{{word}}}".format(word=word.strip())
                    headers += "\\\\\n"
                    self.tex += r"""
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
                            self.tex += "{word}".format(word=word.strip())
                        else:
                            self.tex += " & {word}".format(word=word.strip())

                    self.tex += "\\\\\n"

        self.tex += "\\end{longtable}"
        self.tex = "\n".join(template.insert(1,self.tex))





