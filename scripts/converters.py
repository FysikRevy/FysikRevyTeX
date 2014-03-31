import os
import shutil
import subprocess
import tempfile
import uuid
from multiprocessing import Pool, cpu_count

class Converter:
    def __init__(self, config):
        self.conf = config

    def textopdf(self, tex, pdfname="", outputdir="", repetitions=2, encoding='utf-8'):
        "Generates a PDF from either a TeX file or TeX object."

        if outputdir == "":
            outputdir = self.conf["Paths"]["pdf"]

        src_dir = os.getcwd()

        if type(tex) == str and tex.strip()[-3:] == 'tex':
            # Object is a file path string.
            input_is_tex_file = True
        else:
            input_is_tex_file = False
            temp = tempfile.mkdtemp()


        if input_is_tex_file:
            # Object is a file path string.
            path, texfile = os.path.split(tex.strip())
            pdffile = "{}.pdf".format(texfile[:-4])
            dst_dir = os.path.join(src_dir, outputdir,
                                   os.path.split(path)[1])
        
        elif type(tex) == str and tex.strip()[-3:] != 'tex':
            # Object is a string of TeX code.
            tempname = uuid.uuid4() # Generate unique name
            texfile = "{}.tex".format(tempname)
            pdffile = "{}.pdf".format(tempname)
            dst_dir = os.path.join(src_dir, outputdir)

            with open(os.path.join(temp, texfile), 'w', encoding=encoding) as f:
                f.write(tex)

        elif type(tex).__name__ == "TeX":
            # Object is a TeX object.
            if tex.fname:
                fname = tex.fname[:-4]
            else:
                fname = uuid.uuid4() # Generate unique name
            texfile = "{}.tex".format(fname)
            pdffile = "{}.pdf".format(fname)
            tex.write(os.path.join(temp,texfile), encoding=encoding)
            dst_dir = os.path.join(src_dir, outputdir)

        else:
            raise TypeError("Input should be either TeX code, a string "
                            "of a .tex file or a TeX object.")


        if input_is_tex_file:
            os.chdir(path)
        else:
            os.chdir(temp)
            os.symlink(os.path.join(src_dir,"revy.sty"), "revy.sty")

        for i in range(repetitions):
            if self.conf.getboolean("TeXing","verbose output"):
                rc = subprocess.call(["pdflatex", "-halt-on-error", texfile])
            else:
                rc = subprocess.call(["pdflatex", "-halt-on-error", texfile], 
                                     stdout=subprocess.DEVNULL)

        if pdfname == "":
            pdfname = pdffile
        else:
            os.rename(pdffile, pdfname)

        print("{:<42}".format("\033[0;37;1m{}:\033[0m".format(pdfname)), end="")
        if rc == 0:
            print("\033[0;32m Success!\033[0m")
        else:
            print("\033[0;31m Failed!\033[0m")

        try:
            shutil.move(pdfname, dst_dir)
        except shutil.Error:
            os.remove(os.path.join(dst_dir, pdfname))
            shutil.move(pdfname, dst_dir)

        os.chdir(src_dir)

        if input_is_tex_file:
            os.remove("{}.aux".format(os.path.join(path,texfile[:-4])))
            os.remove("{}.log".format(os.path.join(path,texfile[:-4])))
        else:
            shutil.rmtree(temp)


    def parallel_textopdf(self, file_list, outputdir="", repetitions=2, encoding='utf-8'):

        new_file_list = []
        for el in file_list:
            if type(el) == list and type(el[1]) == str:
                file_path = el[0]
                pdfname = el[1]
            else:
                file_path = el
                pdfname = ""

            # Each element should be: file_path, pdfname, repetitions, encoding
            new_file_list.append((file_path, pdfname, outputdir, repetitions, encoding))

        with Pool(processes = cpu_count()) as pool:
            result = pool.starmap(self.textopdf, new_file_list)

