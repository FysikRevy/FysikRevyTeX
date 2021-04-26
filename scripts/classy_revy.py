import os
from time import localtime, strftime

import base_classes as bc
from tex import TeX

from config import configuration as conf
from pathlib import Path

class Material:
    # TODO: This class should perhaps inherit from the completely general
    # TeX class, as this is basically just a special case of a TeX file.
    # This would make functions easier, as they can treat TeX and
    # Material in the same way.
    def __init__(self, info_dict):
        "Extract data from dictionary returned by parsetexfile()."
        self.title = info_dict["title"]
        try:
            self.status = info_dict["status"]
        except KeyError:
            print("No status on '{}' is set.".format(self.title))
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
        self.category = Path( info_dict["path"] ).parts[0]

        try:
            self.melody = info_dict["melody"]
        except KeyError:
            self.melody = ""

        # Meta data
        self.modification_time = info_dict['modification_time']
        self.has_been_texed = False

        # Save the file content:
        self.tex = info_dict['tex']

        # Stuff that could be used for future features:
        self.appearing_roles = info_dict["appearing_roles"]

        # To be deprecated (most likely):
        try:
            self.author = info_dict["author"]
        except KeyError:
            print("No author for '{}' is declared.".format(self.title))
        self.year = info_dict["revyyear"]
        self.revue = info_dict["revyname"]
        self.version = info_dict["version"]

    @classmethod
    def fromfile(cls, filename):
        "Parse TeX file."
        tex = TeX()
        tex.parse(filename)
        info_dict = tex.info
        info_dict["path"] = filename
        return cls(info_dict)


    def write(self, fname, encoding='utf-8'):
        "Write to a TeX file."
        # FIXME: this pretty much proves that TeX and Material need to be
        # merged somehow.
        with open(fname, 'w', encoding=encoding) as f:
            for line in self.tex:
                f.write(line)

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
    def __init__(self, acts):
        self.acts = acts
        self.actors = []

        # Load variables from the configuration:
        # FIXME: Maybe just pass the ConfigParser object itself? There shouldn't
        # be a reason to reparse the file.
        self.conf = conf
        self.name = self.conf["Revue info"]["revue name"]
        self.year = self.conf["Revue info"]["revue year"]

        # Make a list of all actors:
        for act in self.acts:
            for material in act.materials:
                material.register_actors(self.actors)
        self.actors.sort(key=lambda actor: actor.name)


    @classmethod
    def fromfile(cls, filename, encoding='utf-8'):
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
                            print("You need a name for the act before any TeX file is listed.")
                            print("Problematic file: {}".format(filename))
                            print("Error raised: {}".format(err))

            # Store the very last act:
            acts.append(act)

        r = cls(acts)
        # Hust modifikations-tid for aktoversigten
        r.modification_time = os.stat( filename ).st_mtime
        return r

    def __repr__(self):
        acts = "{}".format(self.acts[0])
        for i in range(1,len(self.acts)):
            acts = "{}\n{}".format(acts, self.acts[i])

        return acts



