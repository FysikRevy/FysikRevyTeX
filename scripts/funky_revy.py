import re
import sys
from IPython import embed

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

    

def parsetexfile(filename, encoding='utf-8'):
    "Parse a TeX file and extract revue relevant information. Returns a dictionary with the information."
    
    # Create dictionary to store relevant information:
    info = {}

    # Create lists for other stuff:
    info["props"] = []
    info["roles"] = []
    info["actual_roles"] = [] # How many people/abbreviations that occur in the actual sketch/song.

    # List of keywords/commands to ignore, i.e. that are not relevant to extract:
    ignore_list = ["documentclass", "usepackage", "begin", "end", "maketitle", "act"]
    # TODO: Should \act really be ignored?

    # List of important keywords/commands:
    important_list = ["prop", "role", "sings", "says"]
    # TODO: Handle \scene in a nice way.

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
                        info[first_part] = end_part

                else:
                    #keyword_start = line.find("{")
                    #command = line[1:keyword_start]
                    #command = cmd_re.findall(line)[0] # Extract (the first) command using regex
                    command = re.findall("\w+", line)[0] # Extract (the first) command using regex

                    if command not in ignore_list:
                        #keyword_end = line.find("}")
                        #keyword = line[keyword_start+1:keyword_end]

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
                                info["props"].append(Prop(prop, responsible, description))

                            elif command == "role":
                                abbreviation = keyword
                                name = opt_re.findall(line)[0]
                                role = eol_re.findall(line)[0]
                                if len(name) > 0:
                                    # Only store the role if it is not empty:
                                    info["roles"].append(Role(abbreviation, name, role))

                            elif command == "sings" or command == "says":
                                # We count how many abbreviations actually appear in the sketch/song
                                # in order to find missing persons in the roles list.
                                abbreviation = keyword
                                if keyword not in info["actual_roles"]:
                                    info["actual_roles"].append(keyword)
                        else:
                            # Store information:
                            info[command] = keyword

    return info


if __name__ == "__main__":

    info = parsetexfile("/home/ks/documents/fysikrevy/jubilæumsrevy13/2013/sange/YBCO.tex")
 
    for key in info.keys():
        print("{}: {}".format(key, info[key]))
