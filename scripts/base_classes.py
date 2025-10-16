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

    def __repr__(self):
        return "{} ({}): {}".format(self.role, self.abbreviation, self.actor)

    def add_material(self, material):
        "Add the Material of the sketch/song the role appears in."
        self.material = material

class Actor:
    def __init__(self, name):
        self.name = name
        self.roles = []
        self.instructorships = []

    def __repr__(self):
        return "{}".format(self.name)

    def add_role(self, role):
        self.roles.append(role)

    def add_instructorship( self, instructorship ):
        self.instructorships.append( instructorship )
