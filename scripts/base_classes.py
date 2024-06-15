class Prop:
    def __init__(self, prop, responsible, description):
        self.prop = prop
        self.responsible = responsible
        self.description = description

    def __repr__(self):
        return "{} ({})".format(self.prop, self.responsible)

class Role:
    def __init__(self, abbreviation, name, role):
        self.abbreviation = abbreviation.strip()
        self.actor = name.strip()
        self.role = role.strip()
        self.material = None
        self.material_path = ""

    def __repr__(self):
        return "{} ({}): {}".format(self.role, self.abbreviation, self.actor)

    def add_material(self, material):
        "Add the Material of the sketch/song the role appears in."
        self.material = material

    def add_material_path(self, path):
        "Add the path of the sketch/song the role appears in."
        self.material_path = path

class Actor:
    def __init__(self, name):
        self.name = name
        self.roles = []

    def __repr__(self):
        return "{}".format(self.name)

    def add_role(self, role):
        self.roles.append(role)
