class Prop:
    def __init__(self, prop, responsible, description):
        self.prop = prop
        self.responsible = responsible
        self.description = description

    def __repr__(self):
        return "{} ({})".format(self.prop, self.responsible)

class Role:
    def __init__(self, abbreviation, name, role):
        self.abbreviation = abbreviation
        self.actor = name
        self.role = role
        self.material = ""

    def __repr__(self):
        return "{} ({}): {}".format(self.role, self.abbreviation, self.actor)

    def add_material(self, material):
        "Add the title of the sketch/song the role appears in."
        self.material = material

class Actor:
    def __init__(self, name):
        self.name = name
        self.roles = []

    def __repr__(self):
        return "{}".format(self.name)

    def add_role(self, role):
        self.roles.append(role)
