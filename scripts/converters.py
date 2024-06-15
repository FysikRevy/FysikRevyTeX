# coding: utf-8
import os
import shutil
import subprocess
import tempfile
import uuid
from multiprocessing import Pool, cpu_count
from time import time
from pathlib import Path
from itertools import takewhile

from config import configuration as conf

# fordi https://learn.microsoft.com/en-us/windows/security/threat-protection/security-policy-settings/create-symbolic-links
# tak, windows.
try:
    import _winapi
    def portable_dir_link( source, target ):
        _winapi.CreateJunction( source, target )
except ImportError:
    def portable_dir_link( source, target ):
        os.symlink( source, target )
        
class ConversionError( Exception ):
    pass
        
class Converter:
    def __init__(self):
        self.conf = conf

    def textopdf(self, *args, **kwargs):
        """
        Dummy wrapper method to make multiprocessing work on a 
        decorated function.
        """
        self._textopdf(*args, **kwargs)

    def _textopdf(self, tex, pdfname="", outputdir="", repetitions=2, encoding='utf-8'):
    #def textopdf(self, tex, pdfname="", outputdir="", repetitions=2, encoding='utf-8'):
        "Generates a PDF from either a TeX file or TeX object."

        if outputdir == "":
            outputdir = self.conf["Paths"]["pdf"]

        src_dir = os.getcwd()
        src_modtime = time()    # Gå ud fra helt ny

        if type(tex) == str and tex.strip()[-3:] == 'tex':
            # Object is a file path string.
            input_is_tex_file = True
            src_modtime = os.stat( tex ).st_mtime
        else:
            input_is_tex_file = False
            temp = tempfile.mkdtemp()

        if input_is_tex_file:
            # Object is a file path string.
            # The TeXing should be done in the original directory to avoid
            # problems with e.g. included figures not being copied to the
            # temporary directory.
            path, texfile = os.path.split(tex.strip())
            pdffile = "{}.pdf".format(texfile[:-4])
            dst_dir = os.path.join(src_dir, outputdir,
                                   os.path.relpath( path, src_dir ))
        
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
            src_modtime = tex.info[ "modification_time" ]
            tex.write(os.path.join(temp,texfile), encoding=encoding)
            dst_dir = os.path.join(src_dir, outputdir)

        elif type(tex).__name__ == "Material":
            # Object is a Material object.
            # The TeXing should be done in the original directory to avoid
            # problems with e.g. included figures not being copied to the
            # temporary directory.
            path, texfile = os.path.split(tex.path.strip())
            pdffile = "{}.pdf".format(texfile[:-4])
            dst_dir = os.path.join(src_dir, outputdir,
                                   os.path.relpath( path, src_dir ))
            input_is_tex_file = True
            src_modtime = tex.modification_time

        else:
            raise TypeError("Input should be either TeX code, a string of a "
                            ".tex file, a TeX object or a Material object.")

        try:
            if ( os.stat( os.path.join(dst_dir, pdfname or pdffile ) ).st_mtime
                 > src_modtime
                 and not self.conf.getboolean( "TeXing", "force TeXing of all files" )
                ):
                return          # hop fra, når output er nyere end input
        except FileNotFoundError:
            # outputfilen findes ikke. Vi laver den
            pass                

        if input_is_tex_file:
            os.chdir(path)
        else:
            os.chdir(temp)
            if os.path.exists( os.path.join( src_dir, "revy.sty" ) ):
                shutil.copy(os.path.join(src_dir,"revy.sty"), "revy.sty")
            portable_dir_link( src_dir, "src_dir" )

        for i in range(repetitions):
            if self.conf.getboolean("TeXing","verbose output"):
                rc = subprocess.call(["pdflatex", "-interaction=nonstopmode", texfile])
            else:
                rc = subprocess.call(["pdflatex", "-interaction=batchmode", texfile], 
                                     stdout=subprocess.DEVNULL)


        # Check whether the pdf was generated:
        # TODO: This needs to be done better.
        # if not os.path.isfile(pdffile):
        #     rerun = input("Oh snap! Something went wrong when creating the PDF.\n"
        #                   "Do you want to run pdflatex again, this time with output? (y/[n])")
        #     if rerun == 'y':
        #         rc = subprocess.call(["pdflatex", texfile]) 


        print("{:<42}".format("\033[0;37;1m{}:\033[0m".format(pdfname or pdffile)), end="")
        if rc == 0:
            print("\033[0;32m Success!\033[0m")
        elif os.path.exists( pdffile ):
            print("\033[0;33m Had Errors!\033[0m" )
        else:
            print("\033[0;31m Failed!\033[0m")
            raise ConversionError

        if pdfname == "":
            pdfname = pdffile
        else:
            os.rename(pdffile, pdfname)

        try:
            if not os.path.isdir( dst_dir ):
                os.makedirs( dst_dir )
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

            new_file_list.append((file_path, pdfname, outputdir, repetitions, encoding))

        with Pool(processes = cpu_count()) as pool:
            result = pool.starmap(self.textopdf, new_file_list)

    def tex_to_wordcount(self, tex_file ):

        try:
            tex_file = Path( tex_file )
        except TypeError as e:
            e.args = ("for argument tex_file",) + e.args
            raise e

        with tempfile.TemporaryDirectory() as temp:
            temp = Path( temp )
            r = subprocess.run(( "pdflatex",
                                 "-aux-directory={}".format( temp ),
                                 "-output-directory={}".format( temp ),
                                 "scripts/revywordcount.tex"),
                               timeout = 60,
                               input = str( tex_file.absolute() ),
                               text = True,
                               encoding = 'utf-8',
                               stdout = subprocess.DEVNULL
                               )
            try:
                with ( temp / "revywordcount.log" ).open() as f:
                    counts = {}

                    def type_dispatch( line ):
                        if "3.08641" in line:
                            return start_counting( "sung" )
                        if "3.08643" in line:
                            return start_counting( "spoken" )

                    def start_counting( linetype ):
                        role = "".join(
                            [ line[-2:-1] for line
                              in takewhile(
                                  lambda line: not "\\3.08632 :" in line\
                                           and not "\\3.08632 (" in line,
                                  f
                              )
                              if "\\3.08632" in line
                             ]
                        )
                        if not role in counts:
                            counts[role] = {"spoken": 0, "sung": 0}
                        for line in f:
                            if "3.08633" in line or "3.08635" in line:
                                counts[role][linetype] += 1
                            if "3.0864" in line:
                                return type_dispatch( line )

                    for line in f:
                        type_dispatch( line )

                    return counts
            except FileNotFoundError:
                # ¯\_(ツ)_/¯
                return {}
