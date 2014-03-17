import re
from IPython import embed

from classy_revy import Prop, Role

# Regular expression that extracts everything between \ and {:
cmd_re = re.compile(r"^.*\\(.*){.*$")

# Regular expression that extracts everything between { and }:
kw_re = re.compile(r"^.*{(.*)}.*$")

# Regular expression that extracts everything between [ and ]:
opt_re = re.compile(r"^.*\[(.*)\].*$")

# Regular expression that extracts everything ] and to the end of the line:
eol_re = re.compile(r"^.*\](.*).*$")

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
        for line in f.readlines():
            line = line.strip() # Remove leading and trailing whitespaces
            if len(line) > 0 and line[0] == '\\': # only look for a command

                if "{" not in line:
                    # If it is a strange line, extract the first part (everything until the
                    # first non-alphanumeric character that isn't '\':
                    first_part = re.findall("\w+", line)[0]

                    # Find also the second part, i.e. whatever follows the first part (including
                    # the non-alphanumeric character):
                    end_part = re.findall("^.\w+(.*)", line)[0]

                    # Store the info:
                    info[first_part] = end_part

                else:
                    #keyword_start = line.find("{")
                    #command = line[1:keyword_start]
                    command = cmd_re.findall(line)[0] # Extract (the first) command using regex

                    if command not in ignore_list:
                        #keyword_end = line.find("}")
                        #keyword = line[keyword_start+1:keyword_end]

                        keyword = kw_re.findall(line)[0] # Extract (the first) keyword using regex
                        
                        # Now check whether the command is one of the important ones:
                        if command in important_list:
                            if command == "prop":
                                prop = keyword
                                responsible = opt_re.findall(line)[0]
                                info["props"].append(Prop(prop, responsible))

                            elif command == "role":
                                abbreviation = keyword
                                name = opt_re.findall(line)[0]
                                role = eol_re.findall(line)[0]
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
