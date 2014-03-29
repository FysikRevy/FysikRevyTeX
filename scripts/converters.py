import shutil
import subprocess
import tempfile

class Converter:
    def __init__(self, config):
        self.conf = config

    def textopdf(tex, pdfname="", repetitions=2, encoding='utf-8'):
        "Generates a PDF from either a TeX file or TeX object."

        print("{:<25}".format("\033[0;37;1m{}:\033[0m".format(pdfname)), end="")

        current_dir = os.getcwd()
        temp = tempfile.mkdtemp()

        if type(tex) == str and tex.strip()[-3:] == 'tex':
            # Object is a file.
            shutil.copy(tex, temp)
            texfile = tex
            pdffile = "{}.pdf".format(tex[:-4])
        
        elif type(tex) == str and tex.strip()[-3:] != 'tex':
            # Object is a string of TeX code.
            tempname = uuid.uuid4() # Generate unique name
            texfile = "{}.tex".format(tempname)
            pdffile = "{}.pdf".format(tempname)
            with open(os.path.join(temp, texname), 'w', encoding=encoding) as f:
                f.write(tex)

        elif type(tex).__name__ == "TeX":
            # Object is a TeX object.
            if tex.fname:
                fname = tex.fname
            else:
                fname = uuid.uuid4() # Generate unique name
            texfile = "{}.tex".format(fname)
            pdffile = "{}.pdf".format(fname)
            tex.write(os.path.join(temp,texfile), encoding=encoding)


        os.chdir(temp)
        os.symlink(os.path.join(current_dir,"revy.sty"), "revy.sty")
            
        for i in range(repetitions):
            if self.conf["TeXing"]["verbose output"]:
                rc = subprocess.call(["pdflatex", "-halt-on-error", texfile])
            else:
                rc = subprocess.call(["pdflatex", "-halt-on-error", texfile], stdout=subprocess.DEVNULL)

        if rc == 0:
            print("\033[0;32m Success!\033[0m")
        else:
            print("\033[0;31m Failed!\033[0m")

        if pdfname == "":
            pdfname = pdffile
        else:
            os.rename(pdffile, pdfname)

        shutil.copy(pdfname, os.path.join(current_dir,self.conf["Paths"]["pdf"]))
        os.chdir(current_dir)
        shutil.rmtree(temp)

    def _textopdf_unpack(self, args):
        self.textopdf(args[0], args[1], args[2])

    def parallel_textopdf(self, file_list, repetitions=2, encoding='utf-8'):

        new_file_list = []
        for el in file_list:
            new_file_list.append(el, repetitions, encoding)

        with Pool(processes = cpu_count()) as pool:
            result = pool.starmap(self._textopdf_unpack, new_file_list)

