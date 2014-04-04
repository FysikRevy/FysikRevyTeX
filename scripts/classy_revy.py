import os
from configparser import ConfigParser
from time import localtime, strftime

import base_classes as bc
from tex import TeX

class Material:
    def __init__(self, info_dict):
        "Extract data from dictionary returned by parsetexfile()."
        self.title = info_dict["title"]
        self.status = info_dict["status"]
        self.props = info_dict["props"]
        self.length = info_dict["eta"].replace('$','').split()[0]
        self.path = os.path.abspath(info_dict["path"])
        self.roles = info_dict["roles"]
        try:
            self.responsible = info_dict["responsible"]
        except KeyError:
            print("No TeX responsible for '{}'.".format(self.title))
            self.responsible = ""

        for role in self.roles:
            # Add the title of this material to the roles:
            #role.add_material(self.title)
            role.add_material_path(self.path)
        
        # Extract the category (which is the directory):
        path, self.file_name = os.path.split(self.path)
        self.category = os.path.split(path)[1]

        try:
            self.melody = info_dict["melody"]
        except KeyError:
            self.melody = ""
        
        # Stuff that could be used for future features:
        self.appearing_roles = info_dict["appearing_roles"]

        # To be deprecated (most likely):
        self.author = info_dict["author"]
        self.year = info_dict["revyyear"]
        self.revue = info_dict["revyname"]
        self.version = info_dict["version"]
    
    @classmethod
    def fromfile(cls, filename):
        "Parse file using parsetexfile()."
        tex = TeX()
        tex.parse(filename)
        info_dict = tex.info
        info_dict["path"] = filename
        return cls(info_dict)

    def __repr__(self):
        return "{} ({} min): {}".format(self.title, self.length, self.status)

    def register_actors(self, list_of_actors):
        "Takes a list of actors and updates it with the actors in the sketch/song."

        for role in self.roles:
            for actor in list_of_actors:
                if role.actor == actor.name:
                    # If the actor exists in the list, we add this role to him/her:
                    actor.add_role(role)
                    break
            else:
                # If not, we create a new actor and update the list:
                actor = bc.Actor(role.actor)
                actor.add_role(role)
                list_of_actors.append(actor)


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
        
        l = "{:4.2f}".format(t)
        for key in n:
            if n[key] != 1:
                l += " + {}{}".format(n[key],key)
            else:
                l += " + {}".format(key)

        return l



class Revue:
    def __init__(self, acts, config_file = "revytex.conf"):
        self.acts = acts
        self.actors = []

        # Load variables from the configuration:
        self.conf = ConfigParser()
        self.conf.read(config_file)
        self.name = self.conf["Revue info"]["revue name"]
        self.year = self.conf["Revue info"]["revue year"]

        # Make a list of all actors:
        for act in self.acts:
            for material in act.materials:
                material.register_actors(self.actors)
        self.actors.sort(key=lambda actor: actor.name)


    @classmethod
    def fromfile(cls, filename, encoding='utf-8', config_file = "revytex.conf"):
        "Takes a plan file and extracts the information for each material."
        
        acts = []
        act = Act()

        with open(filename, mode='r', encoding=encoding) as f:
            for line in f.readlines():
                line = line.rstrip()
                if len(line) > 0 and line[0] != "#":
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
                            m = Material.fromfile(line)
                            for role in m.roles:
                                role.add_material(m)
                            act.add_material(m)
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



