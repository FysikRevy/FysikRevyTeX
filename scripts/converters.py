# coding: utf-8
import os
import shutil
import subprocess
import tempfile
import uuid
from os import getpid
from multiprocessing import Pool, cpu_count
from time import time,sleep
from pathlib import Path
from itertools import takewhile, cycle

from config import configuration as conf
from pool_output import \
    PoolOutputManager, text_effect, print_columnized, indices, task_start

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

class Output:
    def begin( self, pid, taskname ):
        self.taskname = "{:<42}".format(
            "\033[0;37;1m{}:\033[0m".format(taskname)
        )
    def activity( self, pid, number ):
        pass
    def skipped( self, pid ):
        pass
    def success( self, pid ):
        print( self.taskname + "\033[0;32m Success!\033[0m" )
    def done_with_warnings( self, pid ):
        print( self.taskname + "\033[0;33m Had Errors!\033[0m" )
    def failed( self, pid ):
        print( self.taskname + "\033[0;31m Failed!\033[0m" )
        
class Converter:
    def __init__(self):
        self.conf = conf

    def textopdf(self, *args, **kwargs):
        """
        Dummy wrapper method to make multiprocessing work on a 
        decorated function.
        """
        return self._textopdf(*args, **kwargs)

    def _textopdf(self,
                  tex,
                  pdfname="",
                  outputdir="",
                  repetitions=2,
                  encoding='utf-8',
                  output=Output()
                  ):
    #def textopdf(self, tex, pdfname="", outputdir="", repetitions=2, encoding='utf-8'):
        "Generates a PDF from either a TeX file or TeX object."

        output.begin( getpid(), pdfname or tex )

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
                output.skipped( getpid() )
                # hop fra, når output er nyere end input
                return (None, pdfname or pdffile) 
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

        # for i in range(repetitions):
        #     if self.conf.getboolean("TeXing","verbose output"):
        #         rc = subprocess.call(["pdflatex", "-interaction=nonstopmode", texfile])
        #     else:
        #         rc = subprocess.call(["pdflatex", "-interaction=batchmode", texfile], 
        #                              stdout=subprocess.DEVNULL)
        rc = None
        for i in range(repetitions):
            tex_proc = subprocess.Popen(
                ["pdflatex", "-interaction=nonstopmode", texfile],
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
                text = True)
            while True:
                o,e = "",""
                try:
                    o,e = tex_proc.communicate( timeout = 1 )
                except subprocess.TimeoutExpired:
                    pass
                else:
                    output.activity(
                        getpid(),
                        sum( 1 for c in o if c == '\n' )
                    )
                    # TODO: useless, really...
                    if self.conf.getboolean( "TeXing", "verbose output" ):
                        print( o )
                rc = tex_proc.returncode
                if rc != None:
                    break

        # Check whether the pdf was generated:
        # TODO: This needs to be done better.
        # if not os.path.isfile(pdffile):
        #     rerun = input("Oh snap! Something went wrong when creating the PDF.\n"
        #                   "Do you want to run pdflatex again, this time with output? (y/[n])")
        #     if rerun == 'y':
        #         rc = subprocess.call(["pdflatex", texfile]) 

        try:
            try:
                if not os.path.exists( pdffile ):
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

            finally:
                os.chdir(src_dir)

                if input_is_tex_file:
                    os.remove("{}.aux".format(os.path.join(path,texfile[:-4])))
                    os.remove("{}.log".format(os.path.join(path,texfile[:-4])))
                    output.activity( getpid(), 1 )
                else:
                    shutil.rmtree(temp)
                    output.activity( getpid(), 1 )
                
        except Exception as e:
            output.failed( getpid() )
            return (e, pdfname or pdffile)
        finally:
            os.chdir( src_dir )
            
        if rc == 0:
            output.success( getpid() )
        else:
            output.done_with_warnings( getpid() )
        return (rc, pdfname or pdffile)


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

        with Pool(processes = cpu_count()) as pool,\
             PoolOutputManager() as man:
            po = man.PoolOutput( cpu_count() )
            po.queue_add( *( a[1] if a[1] else a[0] for a in new_file_list ) )
            new_file_list = [ f + ( po, ) for f in new_file_list ]
            result = pool.starmap_async(self.textopdf, new_file_list)
            while not result.ready():
                sleep( 1 )
                po.refresh()
            po.clonk()
            print()
            fail, fail_other, err, done, skip = [],[],[],[],[]
            for ind,r in zip( cycle( indices ), result.get() ):
                ro = [ (ind,) + r ]
                match r[0]:
                    case None:
                        skip += ro
                    case 0:
                        done += ro
                    case int():
                        err += ro
                    case ConversionError():
                        fail += ro
                    case _:
                        fail_other += ro
            if fail:
                print( "\nFølgende filer kunne ikke produceres pga. "\
                       + text_effect( "kompileringsfejl", "error" )\
                       + ":" )
                print_columnized( *(
                    ( len( f ) + 3, task_start( i + ": " ) + f )
                    for i,_,f in fail
                ))
            if fail_other:
                print( "\nFølgende filer kunne ikke produceres pgs. "\
                       + text_effect( "andre fejl", "error" ) + "." )
                for i,e,f in fail_other:
                    print( task_start( i + ": " ) + f )
                    print( repr( e ) )
            if err:
                print( "\nFølgende filer kunne produceres, men med "\
                       + text_effect( "none", "warn" ) + ":"
                      )
                print_columnized( *(
                    ( len( f ) + 3, task_start( i + ": " ) + f )
                    for i,_,f in err
                ))
            print()
            if done:
                print( ( "{} filer blev " \
                         + text_effect( "korrekt kompileret", "success" ) + "."
                        ).format( len( done ))
                      )
            if skip:
                print( ("{} filer havde ingen opdateringer, og blev "\
                        + text_effect( "sprunget over", "skip" ) + "."
                        ).format( len( skip ))
                      )

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
