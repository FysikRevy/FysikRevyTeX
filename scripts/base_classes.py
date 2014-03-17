class Prop:
    def __init__(self, prop, responsible):
        self.prop = prop
        self.responsible = responsible

    def __repr__(self):
        return "{} ({})".format(self.prop, self.responsible)

class Role:
    def __init__(self, abbreviation, name, role):
        self.abbreviation = abbreviation
        self.name = name
        self.role = role

    def __repr__(self):
        return "{} ({}): {}".format(self.role, self.abbreviation, self.name)

class Actor:
    # FIXME: Unneeded?
    def __init__(self, name):
        self.name = name
        self.roles = []

    def add_role(self, role):
        self.roles.append(role)
