# -*- coding: utf-8 -*-
import os
import re
import sys
import locale
import re
from time import localtime, strftime
from pathlib import Path
from functools import cmp_to_key
from datetime import timedelta
from copy import copy
from itertools import cycle

from ordered_set import OrderedSet

from base_classes import Prop, Role, NinjaProp
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

# comments
cmt_re = re.compile( r"%.*" )

# RegEx til at splitte tekst-lister, fx ( a, b + c og d ):
text_list_re = re.compile(r'\W*(?:\+|\\&|[oO]g|,)\W*')

class NinjaParser:
   n_args = 4
   re_to_open = re.compile(r"^[^{]*")
   def __init__(self):
      self.parsing = False
      self.parsingProp = False
      self.hardness = ""
      self.name = ""
      self.args = []
      self.bracketDepth = 0

   def parseline(self, line, into):
      line = cmt_re.sub( "", line )
      if not self.parsing:
         if not "\\ninjas" in line:
            return

         self.parsing = True
         line = re.sub( r"^.*?\\ninjas\s*{", "", line, count=1)

      if not self.parsingProp:
         if not "\\prop" in line:
            self.parsing = not re.match( r"^\s*}", line )
            return
         line = re.sub( r"^.*?\\prop\s*{", "", line, count=1 )
         self.parsingProp = True
         self.args += [""]
         self.bracketDepth = 1
         
      if re.match( r"\s*$", line ):
         return

      if self.bracketDepth <= 0:
         line = self.re_to_open.sub( "", line, count=1 )
         if not line or line[0] != "{":
            return
         line = line[1:]
         self.bracketDepth = 1

      i = 0
      while self.bracketDepth > 0 and i < len( line ):
         match line[i]:
            case "{":
               self.bracketDepth += 1
            case "}":
               self.bracketDepth -= 1
         i += 1
      self.args[-1] += line[: i ]
      if self.bracketDepth <= 0:
         # remove newlines and the closing bracket
         self.args[-1] = self.args[-1].replace("\n", "")[:-1]
         if len( self.args ) >= self.n_args:
            self.write_args( into )
            self.parsingProp = False
            self.args = []
         else:
            self.args += ['']
         
      return self.parseline( line[i:], into )

   def parseMove( self, move ):
      parsedMoves = []
      while "\\move" in move:
         parsedMove = []
         move = re.sub( r"^.*?\\move", "", move, count=1 )
         while len( parsedMove ) < 3:
            move = self.re_to_open.sub( "", move, count=1 )
            bracketDepth = i = 1
            while bracketDepth > 0 and i < len( move ):
               match move[i]:
                  case "{":
                     bracketDepth += 1
                  case "}":
                     bracketDepth -= 1
               i += 1
            parsedMove += [ move[1:i-1].strip() ]
            move = move[i:]
         parsedMoves += [ parsedMove ]

      for parsedMove in parsedMoves:
         # print( parsedMove[2] )
         parsedMove[2] = re.findall( r"\\ninja{([^}]*)}", parsedMove[2] )

      return parsedMoves

   def write_args( self, into ):
      ninjaProp = NinjaProp(
         hardness = self.args[0].strip(),
         name = self.args[1].strip(),
         drawing = self.args[2].strip(),
         moves = self.parseMove( self.args[3] )
      )
      into["ninjaprops"] += [ ninjaProp ]

def sublist(lst1, lst2):
   ls1 = [element for element in lst1 if element in lst2]
   ls2 = [element for element in lst2 if element in lst1]
   return OrderedSet( ls1 ) == OrderedSet( ls2 )

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

        return self

    def write(self, fname, encoding='utf-8'):
        "Write to a TeX file."
        with open(fname, 'w', encoding=encoding) as f:
            for l in self:
                f.write( l )

        self.info[ "modification_time" ] = os.path.getmtime( fname )
        return self

    def __iter__(self):
        if 'tex' in self.info:
            yield from self.info['tex']
        else:
            yield self.tex

    def parse(self, fname, encoding='utf-8'):
        "Parse a TeX file and extract revue relevant information to a dictionary."

        self.fname = os.path.split(fname)[1]
        self.fullpath = os.path.abspath( fname )
        self.info['modification_time'] = os.stat(fname).st_mtime

        with open(fname, mode='r', encoding=encoding) as f:
            lines = f.readlines()

        try:
           return self.parse_lines( lines )
        except Exception as e:
           e.add_note( "Was parsing {}".format( fname ) )
           raise e

    def parse_lines( self, lines ):
        "Parse a list of lines of TeX, and extract the info_dict"

        if isinstance( lines, str ):
           raise TypeError("TeX.parse_lines only accepts an iterable of strings, not a single string.")
        ninja_parser = NinjaParser()

        # Create lists for other stuff:
        self.info["props"] = []
        self.info["roles"] = []
        self.info["appearing_roles"] = set() # How many people/abbreviations that occur in the actual sketch/song.
        self.info["instructors"] = []
        self.info["ninjaprops"] = None

        # List of keywords/commands to ignore, i.e. that are not relevant to extract:
        ignore_list = ["documentclass", "usepackage", "maketitle", "act", "scene", "#"]
        # some fool (it's me...) has given \role different meanings in
        # the roles environment and the setch/song environments. thus,
        # we have to keep track of what environment we're in now.
        environment_stack = []

        # Store the file content:
        self.info['tex'] = lines
        # TODO: so, should the class TeX hold complete, TeX-able
        # documents, or just collections of TeX code? There's no way
        # of composing them into TeX-able documents if the latter. But
        # there's no way of validating TeX-ability if the
        # former. We'll either throw away valid documents, or hold
        # invalid ones.
        # Clearly, this represents a failure of the class system abstraction.
        # Who wants do do a major refactoring to fix that?
        # Anyone?

        for n,line in enumerate(lines):
            line = line.strip() # Remove leading and trailing whitespaces
            if ninja_parser.parsing:
               ninja_parser.parseline( line, self.info )
            elif len(line) > 0 and line[0] == '\\': # only look for a command

                if "{" not in line:
                    # If it is a strange line, extract the first part (everything until the
                    # first non-alphanumeric character that isn't '\':
                    try:
                        # Hashtags are ignored also
                        first_part = re.findall(r"[#\w]+", line)[0]
                    except IndexError:
                        # couldn't find a command, just ignore it
                        pass
                    else:
                        # if they write \instructor[title] name
                        if first_part == "instructor":
                            opt = opt_re.search( line )
                            title = opt[1] if opt else "Instruktør"
                            self.info[ "instructors" ] += [
                                Role( title[0].lower(),
                                      eol_re.search( line )[1] if opt \
                                        else re.search(r"^.\w+(.*)", line)[1]\
                                               .strip(),
                                      title
                                     )
                            ]
                        elif first_part not in ignore_list:
                            # Find also the second part, i.e. whatever follows the first part (including
                            # the non-alphanumeric character):
                            end_part = re.findall(r"^.[#\w]+(.*)", line)
                            
                            # Store the info:
                            if end_part:
                               self.info[first_part] = end_part[0]
                               # otherwise ignore it

                else:
                    try:
                        command = re.findall(r"\w+", line)[0] # Extract (the first) command using regex
                    except IndexError:
                        command = ""

                    if command not in ignore_list:
                        if command == "ninjas":
                           self.info[ "ninjaprops" ] = []
                           ninja_parser.parseline( line, self.info )
                           continue

                        try:
                            keyword = kw_re.findall(line)[0].strip() # Extract (the first) keyword using regex
                        except IndexError:
                            # There is no ending '}' in the line.
                            keyword = extract_multiple_lines(lines, n)

                        # Now check whether the command is one of the important ones:
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
                            # are we in a roles environment?
                            # we should never be in a song or sketch environment
                            # *inside* a roles environment, but we'll check to
                            # be sure
                            try:
                               role_level = environment_stack.index( "roles" )
                            except ValueError:
                               continue
                            if "song" in environment_stack[ :role_level ]\
                                or "sketch" in environment_stack[ :role_level ]:
                               continue

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

                        # if they write \instructor[title]{name}
                        elif "instructor" in command:
                            opt = opt_re.search( line )
                            title = opt[1] if opt else "Instruktør"
                            self.info["instructors"] += [
                                Role( title[0].lower(),
                                      kw_re.search( line )[1],
                                      title
                                     )
                            ]

                        elif command in ("sings", "says", "does"):
                            # We count how many abbreviations actually appear in the sketch/song
                            # in order to find missing persons in the roles list.
                            abbreviations = \
                              ( abbr.strip() for abbr in \
                                  re.split( text_list_re, keyword )
                                if not abbr.strip().lower() == "alle"
                               )
                            self.info["appearing_roles"].update( abbreviations )

                        elif command == "begin":
                           environment_stack.insert( 0, keyword )
                        elif command == "end":
                           try:
                              environment_stack.remove( keyword )
                           except ValueError:
                              # the tex is pobably wrong. someone else's problem
                              pass

                        else:
                            if command == "title":
                              try:
                                 self.info["shorttitle"] = \
                                    opt_re.findall( line )[0]
                              except IndexError:
                                 # no optional argument to \title
                                 pass
                            # Store information:
                            self.info[command] = keyword
        return self

    def update_roles( self, roles, instructors=None ):
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

        environment_line_keyword = [
            ( n,
              ( kw_re.search(line)
                or ( None, extract_multiple_lines( self.info["tex"], n ) )
               )[1]
             ) for n,line

            in enumerate( line for line in (
                line.strip() for line in self.info["tex"]
            ))

            if ( line
                 and line[0] == "\\"
                 and "{" in line
                 and ( cmd_re.search( line ) or ( None, "" ) )[1] \
                     in ( "begin", "end" )
                )
        ]
        
        try:
            roles_start, roles_end = [
                n for n,keyword in environment_line_keyword
                if keyword == "roles"
            ]
        except ValueError:
            print("\033[0;31m Failed!\033[0m  "
                  "I was confused by the roles list in {}".format(self.fname)
                  )
            return

        indent = re.search( r"^\s*", self.info['tex'][roles_start + 1] )\
                   .group(0)
                            
        insertions_reversed = [( roles_start, roles_end, [
            indent + "\\role{{{0.abbreviation}}}[{0.actor}] {0.role}\n"\
                      .format( role )
            for role in self.info['roles']
        ])]

        try:
            instr_lines = [
                indent + "\\instructor{} {}\n".format(
                    "[{}]".format( instr.role ) if instr.role else "",
                    instr.actor
                ) for instr in instructors
            ]
        except TypeError:
            # instructors was Null, skip
            pass
        else:
            try:
                instr_start, instr_end = [
                    n for n,keyword in environment_line_keyword
                    if keyword == "instructors"
                ]
            
            except ValueError:
                if any( keyword == "instructors" for n,keyword
                        in environment_line_keyword
                       ):
                    print("\033[0;31m Failed!\033[0m  "
                          "I was confused by the instructors list in {}"\
                          .format(self.fname)
                          )
                    return

                # no instructors environment; make one just after roles
                instr_start = roles_end
                instr_end = roles_end + 1
                if instr_lines:
                    instr_lines = [ "\\begin{instructors}\n" ]\
                        + instr_lines\
                        + [ "\\end{instructors}\n" ]
            else:
               if not instr_lines:
                  # delete the environment
                  instr_start -= 1
                  instr_end += 1

            if not sublist(
                    [ roles_start, roles_end ],
                    sorted([ roles_start, roles_end, instr_start, instr_end ])
            ):
                print("\033[0;31m Failed!\033[0m  "
                      "roles and/or instructors delimiters out of order in "
                      "{}".format(self.fname)
                      )
                return

            insertions_reversed = \
                [( instr_start, instr_end, instr_lines )] + insertions_reversed
            if instr_start < roles_start:
                insertions_reversed = reversed( insertions_reversed )

        for start, end, lines in insertions_reversed:
            self.info["tex"] = self.info["tex"][ : start + 1]\
                + lines\
                + self.info["tex"][ end : ]

        return self
        

    def topdf(self, pdfname, outputdir="", repetitions=2, encoding='utf-8'):
        "Convert internally stored TeX code to PDF using pdflatex."

        converter = cv.Converter()
        converter.textopdf(self, pdfname, outputdir, repetitions, encoding)

        return self

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
                        "}}}}}}\n".format(act_title=act.name, act_length=act.get_length(conf["TeXing"].getboolean("stubs in outline"))))
            self.tex += "\\begin{enumerate}\n"

            ms = act.scenes \
               if conf["TeXing"].getboolean("stubs in outline") \
               else act.materials
            for m in ms:
                self.tex += "\t\\item"

                numcat = re.split( r"\s*,\s*",
                                   conf["Outline"]["numbered categories"]
                                  )
                if numcat != [""] and not m.category in numcat:
                   self.tex += "[\\textsc{{{}}}]".format( m.category.lower() )

                self.tex += " \\textbf{{{title}}} ".format(title = m.title)

                if m.melody:
                    self.tex += "({melody}) ".format(melody=m.melody)

                self.tex += """\\emph{{{revue_name} {revue_year}}}\\\\
        \t\t\\small{{Status: {status}, \\emph{{Tidsestimat: {length} minutter}}}}\n""".format(revue_name=m.revue, revue_year=m.year, status=m.status, length=m.length)

                try:
                   self.info[ "modification_time" ] = max(
                      self.info[ "modification_time" ],
                      m.modification_time
                   )
                except AttributeError:
                   pass

            self.tex += "\\end{enumerate}\n\n"

        template.insert(1,self.tex)
        self.tex = "\n".join(template)

        return self

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

        try:
           template = template.replace(
              "<+COMMA-PLANFILE+>",
              ",planfile={}".format( self.revue.planfile)
           )
        except AttributeError:
           pass

        template = template.replace("<+VERSION+>",
                                    self.conf["Frontpage"]["version"]\
                                    .split(",")[-1]\
                                    .strip()
                                    )
        template = template.replace("<+REVUENAME+>", self.revue.name)
        template = template.replace("<+REVUEYEAR+>", self.revue.year)

        self.tex = template

        return self

    #----------------------------------------------------------------------

    def create_role_overview(self, templatefile="", encoding='utf-8'):

        if self.revue == None:
            raise RuntimeError("The TeX object needs to be instantiated with "
                    "a Revue object in order to use create_role_overview().")

        if templatefile == "":
            templatefile = os.path.join(self.conf["Paths"]["templates"],
                                        "role_overview_template.tex")
        self.tex = ""

        include = re.split( r"\s*,\s*",
                            conf["Role overview"]["include categories"]
                           )
        exclude = re.split( r"\s*,\s*",
                            conf["Role overview"]["exclude categories"]
                           )

        def include_scene( scene ):
           if scene.category in exclude:
              return False
           if not scene.roles \
                 and not scene.category in include \
                 and conf.getboolean("Role overview",
                                     "skip scenes with no roles"):
              print( "Role overview: skipped scene with no roles: {}"\
                     .format( scene.title ) )
              return False
           return True

        roles_acts = [
           { "name": a.name,
             "scenes": [ s for s in a.scenes if include_scene( s ) ]
            } for a in self.revue.acts
        ]
        roles_scenes = [ s for a in roles_acts for s in a["scenes"] ]

        insts = {}
        for mat in roles_scenes:
            for inst in mat.instructors:
                try:
                    if inst.role.lower() not in (
                            name.lower() for name
                            in insts[inst.abbreviation]
                    ):
                        insts[inst.abbreviation] += [ inst.role ]
                except KeyError:
                    insts[inst.abbreviation] = [ inst.role ]

        expls = [ r"\textit{{{}}} = {}".format( k, "/".join( insts[k] ) )
                  for k in insts
                 ]
        if { mat.responsible for mat in roles_scenes } \
           & { a.name for a in self.revue.actors }:
            expls += [ r"\resp{X} = \TeX ansvarlig" + "\n" ]

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
        template[0] = template[0].replace("<+EXPS+>", "\n\n".join(expls) + "\n")

        # Find longest title for pretty printing:
        pad = max(len(m.shorttitle) for act in self.revue.acts \
                  for m in act.materials
                  )
        pad += 2 # Whitespace before and after

        self.tex += r"\actors{"
        for i in range(len(self.revue.actors)):
            # Print actor name left aligned:
            self.tex += "\n    {:<{width}}".format("", width=pad)
            for j in range(i):
                self.tex += "|   "
            self.tex += "@{}".format(self.revue.actors[i])
        self.tex += r"}\\" + "\n\\hline\n"

        for act in roles_acts:
            self.tex += r"\multicolumn{{{width}}}{{|l|}}{{\textbf{{{title}}}}}\\".format(
                    width=len(self.revue.actors)+2, title=act["name"])
            self.tex += "\n\\hline\n"

            for m, mat in enumerate( act["scenes"] ):
                self.tex += "\n{:2d} & {:<{width}}".format(m+1, mat.shorttitle, width=pad)
                for actor in self.revue.actors:
                    for role in actor.roles:
                        if role.material.title == mat.title:
                            rolecell = role.abbreviation
                            if role in actor.instructorships:
                                rolecell = "\\textit{{{}}}".format(rolecell)
                            if actor.name == mat.responsible:
                                rolecell = "\\resp{{{}}}".format(rolecell)
                            self.tex += "&{:>3}".format( rolecell )
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

        return self

    #----------------------------------------------------------------------

    def create_timesheet( self, templatefile="", encoding='utf-8' ):
        if not self.revue:
            raise RuntimeError( "The TeX object needs to be instantiated with "
                    "a Revue object in order to use create_role_overview().")
        self.read( templatefile or (
            Path( self.conf["Paths"]["templates"] ) / "timesheet_template.tex"
        ))
        self.info["modification_time"] = max( self.info["modification_time"],
                                              self.revue.modification_time
                                             )

        front,back = self.tex\
            .replace( "<+VERSION+>", self.conf["Frontpage"]["version"]\
                                         .split(",")[-1]\
                                         .strip()
                     )\
            .replace( "<+REVYNAME+>", self.revue.name )\
            .replace( "<+REVYYEAR+>", self.revue.year )\
            .replace( "<+NACTORS+>", str(len(self.revue.actors)) )\
            .replace( "<+ACTORS+>", "&".join(
                [ "\\actor{{{}}}".format( actor.name )
                  for actor in self.revue.actors
                 ]
            ))\
            .replace( "<+MNTHEIGHT+>",
                      self.conf["Timesheet"]["timesheet scale"]
                     )\
            .split( "<+NUMBERS+>" )
        self.info["tex"] = [ front ]

        for act in self.revue.acts:
            self.info["tex"] += [
                "\\hline&&{{\\bfseries {}}}\\\\\\hline".format( act.name ),
                "\\timescale[y]{{{}}}"\
                .format(
                    ( sum( (m.duration for m in act.scenes), timedelta() )
                      + timedelta( seconds=10 ) * ( len( act.scenes ) - 1 )
                     ) // timedelta( minutes=1 )

                ),
                "&\\tikz{\\draw ",
                " +(0,0) ".join([
                    "[numbertime={{{}:{:0>2}}}{{{}}}{{{}}}]".format(
                        scene.duration // timedelta( minutes=1 ),
                        scene.duration.seconds % 60,
                        scene.duration / timedelta( minutes=1 ),
                        scene.scenechange / timedelta( minutes=1 ) or \
                          conf["TeXing"]["default scene change"]
                    ) for scene in act.scenes ]),
                ";}& \\tikz[remember picture]{ \\draw ",
                " +(0,0) ".join([ "[numbertitle={{{}}}{{{}}}{{{}}}]".format(
                    scene.title,
                    scene.duration / timedelta( minutes=1 ),
                    scene.scenechange / timedelta( minutes=1 ) or \
                      conf["TeXing"]["default scene change"]
                ) for scene in act.scenes ]),
                ";}"
            ]
            for actor in self.revue.actors:
                self.info["tex"] += [
                    "&\\tikz{ \\draw (0,0) ",
                    " +(0,0) ".join([
                        "[" + ( "onstage" if actor.name in
                                ( m_r.actor for m_r in scene.stage_roles )
                                else "offstage" )\
                        + "={{{}}}{{{}}}]"\
                            .format(
                                scene.duration / timedelta( minutes=1 ),
                                scene.scenechange / timedelta( minutes=1 ) \
                                  or conf["Timesheet"]["default scene change"]
                            )
                        for scene in act.scenes
                    ]),
                    ";}"
                ]
            self.info["tex"] += [ "\\\\" ]

        self.info["tex"] += [ back ]

        return self

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

        return self

    #----------------------------------------------------------------------

    def create_frontpage(self, templatefile="", subtitle="", encoding='utf-8'):

        if self.revue == None:
            raise RuntimeError("The TeX object needs to be instantiated with "
                    "a Revue object in order to use create_frontpage().")

        if templatefile == "":
            templatefile = os.path.join(self.conf["Paths"]["templates"],
                                        "frontpage_template.tex")
        if subtitle == "":
            subtitle = "\\TeX{}ster"

        with open(templatefile, 'r', encoding=encoding) as f:
            template = f.read()
        self.info[ "modification_time" ] = max(
            os.stat( templatefile ).st_mtime,
            conf.modification_time # Det er her, vi skriver info til forsiden
        )

        self.tex = template

        self.tex = self.tex.replace("<+SUBTITLE+>", subtitle)

        versions = [ x.strip() for x in
                     self.conf["Frontpage"]["version"].split(",")
                    ]
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

        match re.sub( r'[^a-z]', "", self.revue.name.lower() ):
            case n if "fysikrevy" in n:
                logotype = "\\FysikRevy"
            case n if "satyr" in n:
                logotype = "\\SaTyR{}Revy"
            case _:
                logotype = self.revue.name

        self.tex = self.tex.replace("<+REVUELOGOTYPE+>", logotype )
        self.tex = self.tex.replace("<+REVUENAME+>", self.revue.name)

        self.tex = self.tex.replace("<+REVUEYEAR+>", self.revue.year)
        self.tex = self.tex.replace("<+TOPQUOTE+>",
                            self.conf["Frontpage"]["top quote"])
        self.tex = self.tex.replace("<+BOTTOMQUOTE+>",
                            self.conf["Frontpage"]["bottom quote"])

        return self

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

        return self

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

        return self

    def create_ninja_plan(self, templatefile='templates/ninja_plan_template.tex', encoding='utf-8'):

       self.tex = ""

       dsts = { move.destination
                for scene in self.revue.scenes
                for prop in ( scene.ninjaprops or [] )
                for move in prop.moves
               }
       colors = [ "Thistle", "Goldenrod", "YellowGreen", "Cyan",
                  "VioletRed", "YellowOrange", "SeaGreen", "Orchid" ]
       basetimes = OrderedSet([ "Før", "Under", "Efter" ])
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
                       .replace( "<+NACTORS+>", str( len( self.revue.actors )))
                       .replace( "<+NDSTS+>", str( len( dsts )) )
                       .split( "<+TABLE+>" )
                      )
       self.info[ "modification_time" ] = os.stat( templatefile ).st_mtime
       self.tex += template[0] \
          + "&&&&" \
          + "&".join( "\\actor{{{}}}".format( dst ) for dst in dsts ) \
          + "&" \
          + "&".join( "\\actor{{{}}}".format( actor.name )
                      for actor in self.revue.actors
                     ) \
          + "\\\\\\toprule\n\\endhead\n"
       for an, act in enumerate( self.revue.acts ):
          for mn, mat in enumerate( act.materials ):
             self.tex += \
                "\\multicolumn{{{}}}{{l}}{{({}:{:0>2}) {{\\bfseries {}.{} {}}}}}"\
                 .format( 4 + len( dsts ) + len( self.revue.actors ),
                          mat.duration // timedelta( minutes=1 ),
                          mat.duration % timedelta( minutes=1 ) \
                                      // timedelta( seconds=1 ),
                          an + 1,
                          mn + 1,
                          mat.title
                         )\
                + "\\\\"

             movetimes = OrderedSet(
                [ move.time for prop in ( mat.ninjaprops or [] )
                  for move in prop.moves
                 ]
             )
             markedprops = [ copy( prop ) for prop in ( mat.ninjaprops or [] ) ]
             for prop, col in zip( markedprops, cycle( colors ) ):
                prop.colour = col
             for dst in dsts:
                for n, prop in enumerate(
                      prop for prop in markedprops
                           if dst in [ move.destination for move in prop.moves ]
                ):
                   setattr( prop, dst, n )

             for time in basetimes & movetimes | movetimes:
                timeprops = [
                   [  '&&', '{} \\ninjadif{{{}}}'.format( prop.name,
                                                          prop.hardness
                                                         )
                    ]
                   + [ '\\hspace{{{}ex}}'.format( getattr( prop, dst ) )
                       + '\\tikz[remember picture] \\fill['
                       + prop.colour
                       + '] (0,0) rectangle (1ex, 1em)'# coordinate[pos=.5] ('
                       # + somenumbering ')'
                       + ';'
                       if move.destination == dst else ''
                       for dst in dsts ]
                   + [ ( '\\anactor{'
                         if mat in ( rl.material for rl in actor.roles
                                     if rl not in actor.instructorships )
                         else '\\nonactor{'
                        )
                       + ( prop.colour if actor.name in move.ninjanames else '')
                       + '}'
                       for actor in self.revue.actors ]
                   for prop in markedprops
                   for move in prop.moves
                   if move.time == time
                ]
                timeprops[0][0] = "&&\\sffamily " + time
                for i in range( 2 + len( dsts ), len( timeprops[0] ) ):
                   if len( timeprops ) == 1:
                      timeprops[0][i] += "\\tpbt"
                   else:
                      timeprops[0][i] += "\\top"
                      timeprops[-1][i] += "\\btm"
                      for tp in timeprops[1:-1]:
                         tp[i] += "{}"
                self.tex += \
                   "\n".join([ "&".join( tp ) + '\\\\' for tp in timeprops ])
             self.tex += "\\midrule\n"
       self.tex += template[1]
       return self
