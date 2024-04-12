# -*- coding: utf-8 -*-
import os
import re
import sys
from time import localtime, strftime

from base_classes import Prop, Role
import converters as cv
from helpers import rows_from_csv_etc
# from google_sheets import dump_everything, with_compare

from config import configuration as conf

# Regular expression that extracts everything between \ and {:
cmd_re = re.compile(r"^.*\\([^\{]*){.*$")

# Regular expression that extracts everything between { and }:
kw_re = re.compile(r"^[^}]*{([^}]*)}.*$")

# Regular expression that extracts everything between [ and ]:
opt_re = re.compile(r"^[^\[]*\[([^\]]*)\].*$")

# Regular expression that extracts everything ] and to the end of the line:
eol_re = re.compile(r"^.*\](.*).*$")


def extract_multiple_lines(lines, line_number, start_delimiter='{', end_delimiter='}'):
    "Extract the whole string of a command that spans multiple lines (e.g. \\scene)."

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
    def __init__(self, arg = None):
        # TODO: The following is not needed anymore and should be removed?
        if type(arg).__name__ == "Revue":
            # Load configuration from revue:
            self.revue = arg

        elif arg == None:
            self.revue = None

        else:
            raise TypeError("The optional argument must be "
                            "a Revue object.")

        self.conf = conf

        self.tex = ""
        self.fname = ""

        # Create dictionary to store relevant information:
        self.info = {}


    def read(self, fname, encoding='utf-8'):
        "Read a TeX file without parsing it."
        self.fname = os.path.split(fname)[1]
        self.fullpath = os.path.abspath( fname )
        self.info['modification_time'] = os.stat( fname ).st_mtime
        with open(fname, 'r', encoding=encoding) as f:
            self.tex = f.read()


    def write(self, fname, encoding='utf-8'):
        "Write to a TeX file."
        with open(fname, 'w', encoding=encoding) as f:
            if 'tex' in self.info:
                for l in self.info['tex']:
                    f.write( l )
            else:
                f.write(self.tex)

        self.info[ "modification_time" ] = os.path.getmtime( fname )


    def parse(self, fname, encoding='utf-8'):
        "Parse a TeX file and extract revue relevant information to a dictionary."

        self.fname = os.path.split(fname)[1]
        self.fullpath = os.path.abspath( fname )
        self.info['modification_time'] = os.stat(fname).st_mtime

        # Create lists for other stuff:
        self.info["props"] = []
        self.info["roles"] = []
        self.info["appearing_roles"] = set() # How many people/abbreviations that occur in the actual sketch/song.

        # List of keywords/commands to ignore, i.e. that are not relevant to extract:
        ignore_list = ["documentclass", "usepackage", "begin", "end", "maketitle", "act", "scene"]

        # List of important keywords/commands:
        important_list = ["prop", "role", "sings", "says"]

        with open(fname, mode='r', encoding=encoding) as f:
            lines = f.readlines()

        # Store the file content:
        self.info['tex'] = lines

        for n,line in enumerate(lines):
            line = line.strip() # Remove leading and trailing whitespaces
            if len(line) > 0 and line[0] == '\\': # only look for a command

                if "{" not in line:
                    # If it is a strange line, extract the first part (everything until the
                    # first non-alphanumeric character that isn't '\':
                    try:
                        first_part = re.findall(r"\w+", line)[0]
                    except IndexError:
                        # couldn't find a command, just ignore it
                        pass
                    else:
                        if first_part not in ignore_list:
                            # Find also the second part, i.e. whatever follows the first part (including
                            # the non-alphanumeric character):
                            end_part = re.findall(r"^.\w+(.*)", line)[0]
                            
                            # Store the info:
                            self.info[first_part] = end_part

                else:
                    try:
                        command = re.findall(r"\w+", line)[0] # Extract (the first) command using regex
                    except IndexError:
                        command = ""

                    if command not in ignore_list:

                        try:
                            keyword = kw_re.findall(line)[0].strip() # Extract (the first) keyword using regex
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
                                try:
                                    name = opt_re.findall(line)[0]
                                except IndexError:
                                    # Ikke noget navn endnu
                                    name = ""
                                try:
                                    role = eol_re.findall(line)[0]
                                except IndexError:
                                    #ingen beskrivelse
                                    role = ""

                                if '/' in name:
                                    print("Warning! '/' is not allowed in "
                                          "actor names, but occurs in '{}' "
                                          "in file '{}'. ".format(name,self.fname))
                                    print("It will be replaced by a dash ('-').")
                                    # Replace potential slash with a dash,
                                    # to avoid problems with slashes in filenames.
                                    name = name.replace("/", "-")

                                self.info["roles"].append(Role(abbreviation, name, role))

                            elif command in ("sings", "says", "does"):
                                # We count how many abbreviations actually appear in the sketch/song
                                # in order to find missing persons in the roles list.
                                abbreviations = re.split( r'\W*(?:\+|\\&|[oO]g|,)\W*', keyword )
                                self.info["appearing_roles"].update( abbreviations )
                        else:
                            # Store information:
                            self.info[command] = keyword

    def update_roles( self, roles ):
        """Change the 'roles' section of the tex file to reflect the input list.
        Used for propagating role assignment."""

        for role in roles:
            if not isinstance( role, Role ):
                raise TypeError(
                    # figure that one out!
                    "update_roles passed a role that isn't a Role."
                )

        if not 'tex' in self.info:
            raise RuntimeError( """update_roles called on umparsed TeX object
. My fname is {}""".format( self.fname ) )

        # Match roller efter forkortelser, og sammentræk informationer
        # for roller, som findes i både den nye og den gamle
        # rolleliste
        r = []
        defaults = { "S": "Sanger",
                     "D": "Danser",
                     "B": "Sceneshow"
                    }
        for old_role in self.info['roles']:
            for role in roles:
                if old_role.abbreviation == role.abbreviation:
                    if not role.role:
                        role.role = old_role.role\
                            or defaults.get( role.abbreviation[0] )\
                            or ""
                    r += [ role ]
                    roles.remove( role ) # Det går nok. Vi break'er lige bag efter
                    break
                        
        # Vi går ud fra, at roller, som ikke er i den nye liste, er
        # blevet fjernet fra nummeret
        # Den nye rolleliste er de roller, som var i begge lister plus
        # roller, som kun er i den nye, sorteret efter forkortelse
        self.info['roles'] = r + sorted( roles, key=lambda x: x.abbreviation )

        # find rollesektionen
        for n,whole_line in enumerate( self.info['tex'] ):
            line = whole_line.strip()

            #copy-paste fra parse ^^:
            if len(line) > 0 and line[0] == '\\' and '{' in line:
                command = re.findall(r"\w+", line)[0] # Extract (the first) command using regex
                
                if command in [ "begin", "end" ]:
                    try:
                        keyword = kw_re.findall(line)[0] # Extract (the first) keyword using regex
                    except IndexError:
                        # There is no ending '}' in the line.
                        keyword = extract_multiple_lines(self.info['tex'], n)

                    # end copy-paste
                    # find linjerne, hvor rollelisten starter og slutter
                    if keyword == "roles":
                        if command == "begin":
                            start_line = n
                        if command == "end":
                            end_line = n
                        try: 
                            if start_line and end_line:
                                break
                        except NameError:
                            # ikke endnu
                            pass
        else:
            # der var ikke nogen rolleliste
            # (eller kun en halv, hvilket er værre)
            print("\033[0;31m Failed!\033[0m  No roles list in {}".format(self.fname))
            return

        indent = re.search( r"^\s*", self.info['tex'][start_line + 1] ).group(0)
        
        role_lines = [ indent + "\\role{{{0.abbreviation}}}[{0.actor}] {0.role}\n".format( role )
                       for role in self.info['roles']
        ]
        self.info['tex'] = self.info['tex'][:start_line + 1] + role_lines + self.info['tex'][end_line:]
        

    def topdf(self, pdfname, outputdir="", repetitions=2, encoding='utf-8'):
        "Convert internally stored TeX code to PDF using pdflatex."

        converter = cv.Converter()
        converter.textopdf(self, pdfname, outputdir, repetitions, encoding)


    # def controls(self, controlname):
    #     controlname = controlname.lstrip("\\")
    #     startline = endline = i
    #     startchar = line.find( "\\" + controlname )
    #     pointer = startchar + len( controlname ) + 1
    #     if line[ pointer ] in "[", "(":
    #         line[ pointer + 1: ].split( line[ pointer ] )
    #     [ i, line for i, line in enumerate( self.info['tex'] )
    #       if "\\" + controlname in line ]

    #----------------------------------------------------------------------

    def create_act_outline(self, templatefile="", encoding='utf-8'):
        "Create act outline from Revue object."

        if self.revue == None:
            raise RuntimeError("The TeX object needs to be instantiated with "
                    "a Revue object in order to use create_act_outline().")

        if templatefile == "":
            templatefile = os.path.join(self.conf["Paths"]["templates"],
                                        "act_outline_template.tex")

        self.tex = ""

        with open(templatefile, 'r', encoding=encoding) as f:
            template = f.read().split("<+ACTOUTLINE+>")
        self.info[ "modification_time" ] = max( os.stat( templatefile ).st_mtime,
                                                self.revue.modification_time
                                               )

        template[0] = template[0].replace("<+VERSION+>",
                                          self.conf["Frontpage"]["version"]\
                                              .split(",")[-1]\
                                              .strip()
                                          )
        template[0] = template[0].replace("<+REVUENAME+>", self.revue.name)
        template[0] = template[0].replace("<+REVUEYEAR+>", self.revue.year)

        for act in self.revue.acts:
            self.tex += ("\\section*{{{act_title} \\small{{\\textbf{{"
                        "\\emph{{(Tidsestimat: {act_length} minutter)}}"
                        "}}}}}}\n".format(act_title=act.name, act_length=act.get_length()))
            self.tex += "\\begin{enumerate}\n"

            for m in act.materials:
                self.tex += "\t\\item \\textbf{{{title}}} ".format(title = m.title)

                if m.melody:
                    self.tex += "({melody}) ".format(melody=m.melody)

                self.tex += """\\emph{{{revue_name} {revue_year}}}\\\\
        \t\t\\small{{Status: {status}, \\emph{{Tidsestimat: {length} minutter}}}}\n""".format(revue_name=m.revue, revue_year=m.year, status=m.status, length=m.length)

                self.info[ "modification_time" ] = max(
                    self.info[ "modification_time" ],
                    m.modification_time
                )

            self.tex += "\\end{enumerate}\n\n"

        template.insert(1,self.tex)
        self.tex = "\n".join(template)


    #----------------------------------------------------------------------

    def create_thumbindex(self, templatefile="", encoding='utf-8'):
        "Create a thumbindex outline from Revue object."

        if self.revue == None:
            raise RuntimeError("The TeX object needs to be instantiated with "
                    "a Revue object in order to use create_act_outline().")

        if templatefile == "":
            templatefile = os.path.join(self.conf["Paths"]["templates"],
                                        "thumbindex_template.tex")

        self.tex = ""

        with open(templatefile, 'r', encoding=encoding) as f:
            template = f.read()
        self.info[ "modification_time" ] = max( os.stat( templatefile ).st_mtime,
                                                self.revue.modification_time
                                               )

        template = template.replace("<+VERSION+>",
                                    self.conf["Frontpage"]["version"]\
                                    .split(",")[-1]\
                                    .strip()
                                    )
        template = template.replace("<+REVUENAME+>", self.revue.name)
        template = template.replace("<+REVUEYEAR+>", self.revue.year)

        self.tex = template


    #----------------------------------------------------------------------

    def create_role_overview(self, templatefile="", encoding='utf-8'):

        if self.revue == None:
            raise RuntimeError("The TeX object needs to be instantiated with "
                    "a Revue object in order to use create_role_overview().")

        if templatefile == "":
            templatefile = os.path.join(self.conf["Paths"]["templates"],
                                        "role_overview_template.tex")
        self.tex = ""

        with open(templatefile, 'r', encoding=encoding) as f:
            template = f.read().split("<+ROLEMATRIX+>")
        self.info[ "modification_time" ] = os.stat( templatefile ).st_mtime

        template[0] = template[0].replace("<+VERSION+>",
                                          self.conf["Frontpage"]["version"]\
                                              .split(",")[-1]\
                                              .strip()
                                          )
        template[0] = template[0].replace("<+REVUENAME+>", self.revue.name)
        template[0] = template[0].replace("<+REVUEYEAR+>", self.revue.year)
        template[0] = template[0].replace("<+NACTORS+>", str(len(self.revue.actors)))

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
        self.tex += r"}\\" + "\n" + r"\hline"

        for act in self.revue.acts:
            self.tex += r"\multicolumn{{{width}}}{{|l|}}{{\textbf{{{title}}}}}\\".format(
                    width=len(self.revue.actors)+2, title=act.name)
            self.tex += "\n\\hline\n"

            for m, mat in enumerate(act.materials):
                self.tex += "\n{:2d} & {:<{width}}".format(m+1, mat.title, width=pad)
                for actor in self.revue.actors:
                    for role in actor.roles:
                        if role.material.title == mat.title:
                            if actor.name == mat.responsible:
                                self.tex += "&\\textbf{{\\color{{DodgerBlue}}{:>3}}}".format(role.abbreviation)
                            else:
                                self.tex += "&{:>3}".format(role.abbreviation)
                            break
                    else:
                        self.tex += r"& \q"
                self.tex += "\n" + r"\\\hline"
                self.info[ "modification_time" ] = max(
                    self.info[ "modification_time" ],
                    mat.modification_time
                )

        template.insert(1,self.tex)
        self.tex = "\n".join(template)


    #----------------------------------------------------------------------

    def create_props_list(self, templatefile="", encoding='utf-8'):
        if self.revue == None:
            raise RuntimeError("The TeX object needs to be instantiated with "
                    "a Revue object in order to use create_props_list().")
        if conf["gspread"].getboolean("skip gspread", fallback=False):
            print( "props requires that 'skip gspread' in 'revytex.comf' be set to 'no' or removed. Nothing will be done.")
            return

        from google_sheets import send_props_to_gspread
        send_props_to_gspread( self.revue )



    #----------------------------------------------------------------------

    def create_frontpage(self, templatefile="", subtitle="", encoding='utf-8'):

        if self.revue == None:
            raise RuntimeError("The TeX object needs to be instantiated with "
                    "a Revue object in order to use create_frontpage().")

        if templatefile == "":
            templatefile = os.path.join(self.conf["Paths"]["templates"],
                                        "frontpage_template.tex")
        if subtitle == "":
            subtitle = "tekster"

        with open(templatefile, 'r', encoding=encoding) as f:
            template = f.read()
        self.info[ "modification_time" ] = max(
            os.stat( templatefile ).st_mtime,
            conf.modification_time # Det er her, vi skriver info til forsiden
        )

        self.tex = template

        self.tex = self.tex.replace("<+SUBTITLE+>", subtitle)

        versions = [x.strip() for x in self.conf["Frontpage"]["version"].split(",")]
        self.tex = self.tex.replace("<+VERSION+>", versions[-1] or "??????")
        try:
            self.tex = self.tex.replace(
                "<+VERLIST+>",
                " ".join(
                    [ "\\item[\\rmfamily Tidligere versioner:] {}".format( versions[:-1][0] ) ]
                    + [ "\\item {}".format( x ) for x in versions[1:-1] ]
                )
            )
        except IndexError:
            self.tex = self.tex.replace("<+VERLIST+>", "")

        if self.conf["Revue info"]["revue name"] == "\\FysikRevy\\texttrademark":
            self.tex = self.tex.replace("<+REVUENAME+>", "\\FysikRevy")
        else:
            self.tex = self.tex.replace("<+REVUENAME+>", self.revue.name)

        self.tex = self.tex.replace("<+REVUEYEAR+>", self.revue.year)
        self.tex = self.tex.replace("<+TOPQUOTE+>",
                            self.conf["Frontpage"]["top quote"])
        self.tex = self.tex.replace("<+BOTTOMQUOTE+>",
                            self.conf["Frontpage"]["bottom quote"])


    #----------------------------------------------------------------------

    def create_signup_form(self, templatefile="", encoding='utf-8'):

        if self.revue == None:
            raise RuntimeError("The TeX object needs to be instantiated with "
                    "a Revue object in order to use create_signup_form().")

        if templatefile == "":
            templatefile = os.path.join(self.conf["Paths"]["templates"],
                    "signup_form_template.tex")

        self.tex = ""

        with open(templatefile, 'r', encoding=encoding) as f:
            template = f.read().split("<+SIGNUPFORM+>")
        self.info[ "modification_time" ] = os.stat( templatefile ).st_mtime

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

                self.info[ "modification_time" ] = max(
                    self.info[ "modification_time" ],
                    material.modification_time
                )

            self.tex += "\\end{longtable}\n\n"

        template.insert(1,self.tex)
        self.tex = "\n".join(template)



    #----------------------------------------------------------------------

    def create_contacts_list(self, contactsfile, templatefile='templates/contacts_list_template.tex', encoding='utf-8'):
        """Parses a CSV file to create the contacts list. Comments starting with # will be interpreted as section headings.
    Comments starting with ## will be interpreted as column headers in the list."""

        self.tex = ""

        with open(templatefile, 'r', encoding=encoding) as f:
            template = ( f
                         .read()
                         .replace( "<+VERSION+>",
                                   self.conf["Frontpage"]["version"].
                                   split(",")[-1].strip()
                         )
                         .replace( "<+REVUENAME+>",
                                   self.conf["Revue info"]["revue name"]
                         )
                         .replace( "<+REVUEYEAR+>",
                                   self.conf["Revue info"]["revue year"]
                         )
                         .split("<+CONTACTS+>")
            )
        self.info[ "modification_time" ] = os.stat( templatefile ).st_mtime

        # gæt på, hvad fremtidige TeX-ansvarlige eller
        # kontaktlist-ansvarlige kunne finde på at kalde felterne.
        # udvid gerne, hvis du har flere idéer. Husk, vi kører lower()
        # og fjerner ikke-alfanumeriske tegn, før vi matcher.
        matchers = [ {"rolle","titel","job","ansvar","ansvarspost"},
                     {"navn","fulde navn"},
                     {"øgenavn","kaldenavn","kælenavn","kendtsom"},
                     {"telefonnummer","tel","nummer","telefon","tlf"},
                     {"email","mail"}
        ]

        def determine_format( csv_row ):
            fmt = []
            for m in matchers:
                for i, h in enumerate( csv_row ):
                    if re.sub( "[^a-zæøå0-9]", "", h.lower() ) in m:
                        fmt += [i]
                        break
                else:
                    fmt += [ None ]
            return fmt            

        def interpret_with_format( fmt ):
            def interpret( csv_row ):
                if not any( csv_row ):
                    return ""
                try:
                    return (
                        "\\contact{"
                        + "}{".join(
                            [ csv_row[i].strip().replace( "_", "\\_" )
                              if isinstance( i, int ) else "" for i in fmt ]
                        )
                        + "}\n"
                    )
                except IndexError:
                    return ""
                
            return interpret

        interpret = interpret_with_format( range( len( matchers ) ))
        
        def eat_csv_row( interpret, csv_row ):
            if csv_row[0].startswith( "##" ):
                return (
                    interpret_with_format(
                        determine_format( csv_row )
                    ),
                    []
                )
                
            elif csv_row[0].startswith( "#" ):
                return (
                    interpret_with_format(
                        range(  len( matchers )  )
                    ),
                    [
                        "\\section*{"
                        + csv_row[0][1:].strip()
                        + "}\n"
                    ]
                )
            else:
                return interpret, interpret( csv_row )

        contact_lines = []
        for csv_row in rows_from_csv_etc( contactsfile, encoding=encoding ):
            interpret, cl = eat_csv_row( interpret, csv_row )
            contact_lines += cl

        self.info[ "modification_time" ] = max(
            self.info[ "modification_time" ],
            os.stat( contactsfile ).st_mtime
        )
        self.tex = "".join( template[0:1]
                            + contact_lines
                            + template[1:2]
        )

