from

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

class Material:
    def __init__(self, x, y):
        pass
            
    @classmethod
    def fromdata(cls, info_dict):
        "Extract data from dictionary returned by parsetexfile()."
        

        return cls(data[:,:-1], data[:,-1])
    
    @classmethod
    def fromfile(cls, filename):
        "Parse file using parsetexfile()."
        info_dict = parsetexfile(filename)
        return cls.fromdata(info_dict)
