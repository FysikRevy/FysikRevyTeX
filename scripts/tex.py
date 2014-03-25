
class TeX:
    def __init__(self):
        self.tex = ""


    def read(self, fname):
        "Read a TeX file without parsing it."
        pass

    def write(self, fname):
        "Write to a TeX file."
        pass

    def parse(self, fname):
        "Read a TeX file and parse it."

    def topdf(self, pdfname, repetitions=2):
        "Convert TeX to PDF using pdflatex."
        # Should not take a file name, but convert internal TeX code.
        pass


    def create_act_ouline(self, revue):
        "Create act outline from Revue object."
        pass

    def create_role_overview(self, revue):
        pass

    def create_props_list(self, revue):
        pass

    def create_frontpage(self, revue):
        pass

    def create_signup_form(self, revue):
        pass
    
    def create_contacts_list(self, fname, encoding='utf-8'):
        # TODO: This method has a different interface. Not good!
        pass


