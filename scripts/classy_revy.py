import json
from IPython import embed

from funky_revy import parsetexfile 

class Material:
    def __init__(self, info_dict):
        "Extract data from dictionary returned by parsetexfile()."
        self.title = info_dict["title"]
        self.status = info_dict["status"]
        self.roles = info_dict["roles"]
        self.props = info_dict["props"]
        self.length = info_dict["eta"].replace('$','').split()[0]

        try:
            self.melody = info_dict["melody"]
        except KeyError:
            self.melody = ""
        
        # Stuff that could be used for future features:
        self.appearing_roles = info_dict["actual_roles"]

        # To be deprecated (most likely):
        self.author = info_dict["author"]
        self.year = info_dict["revyyear"]
        self.revy = info_dict["revyname"]
        self.version = info_dict["version"]
    
    @classmethod
    def fromfile(cls, filename):
        "Parse file using parsetexfile()."
        info_dict = parsetexfile(filename)
        return cls(info_dict)

    def __repr__(self):
        return "{} ({} min): {}".format(self.title, self.length, self.status)


class Act:
    def __init__(self):
        self.name = ""
        self.materials = []

    def __repr__(self):
        desc = "{}: {} songs/sketches; {} min in total.\n".format(self.name, len(self.materials), self.get_length())
        for i,m in enumerate(self.materials):
            desc += "  {}. {}\n".format(i+1, m)

        return desc

    def add_name(self, name):
        self.name = name

    def add_material(self, material):
        self.materials.append(material)

    def is_empty(self):
        if len(self.materials) == 0:
            return True
        else:
            return False

    def get_length(self):
        t = 0
        n = {}
        for m in self.materials:
            try:
                t += float(m.length)
            except ValueError:
                try:
                    n[m.length] += 1
                except KeyError:
                    n[m.length] = 1
        
        l = "{}".format(t)
        for key in n:
            l += " + {}{}".format(n[key],key)

        return l



class Revue:
    def __init__(self, acts, config_file = ".config.json"):
        self.acts = acts

        # Load variables from the configuration:
        with open(config_file) as f:
            config = json.load(f)
        self.name = config["revue_name"]
        self.year = config["revue_year"]


    @classmethod
    def fromfile(cls, filename, encoding='utf-8', config_file = ".config.json"):
        "Takes a plan file and extracts the information for each material."
        
        acts = []
        act = Act()

        with open(filename, mode='r', encoding=encoding) as f:
            for line in f.readlines():
                line = line.rstrip()
                if len(line) > 0:
                    if line[-3:] != 'tex':
                        # If not a TeX file, it must be the name of the new act:
                        if act.is_empty():
                            # If the Act is empty, we give it a name:
                            act.add_name(line)
                        else:
                            # If not, we store the current act and create a new:
                            acts.append(act)
                            act = Act()
                            act.add_name(line)
                    else:
                        try:
                            act.add_material(Material.fromfile(line))
                        except NameError as err:
                            print("You need a name for the act before any TeX file.")
                            print("Problematic file: {}".format(filename))
                            print("Error raised: {}".format(err))

            # Store the very last act:
            acts.append(act)

        return cls(acts, config_file = config_file)

    def __repr__(self):
        acts = "{}".format(self.acts[0])
        for i in range(1,len(self.acts)):
            acts = "{}\n{}".format(acts, self.acts[i])

        return acts

