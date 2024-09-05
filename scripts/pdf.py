#import subprocess
import os
import subprocess
from multiprocessing import Pool, cpu_count
from time import sleep
from pathlib import Path

from pypdf import PdfWriter,PdfReader

from config import configuration as conf
from pool_output import PoolOutputManager, Output

class PDF:
    def __init__(self):
        self.conf = conf

    def pdfmerge(self, *args, **kwargs):
        "Dummy wrapper to make multiprocessing work."
        return self._pdfmerge(*args, **kwargs)

    def _pdfmerge(self, file_list, pdfname, output = Output()):
        """Merge a list of PDF files.  file_list kan være en liste med
filnavne, eller en liste med tupler af formatet:
( filnavn, bookmark = None, verso = False )

Hvor filnavn er filnavnet, bookmark er navnet på et pdf-bogmærke (til
indholdsfortegnelsen) og verso angiver, om pdf-filen må starte
på en verso-side i dobbeltsidet layout.

        """
        # det er egentlig noget hø, sådan automagisk at bøje sig rundt
        # om forskellige typer i argumenterne. Det nærmest tigger og
        # be'r om at blive til en bug i fremtiden. Men det giver
        # mening som et format, og bagudkompatibilitet er vigtigt. Så
        # nu er vi her.

        # check, om output er nyere end input
        output.begin( os.getpid(), Path( pdfname ).name )

        try:
            try:
                output_modtime = os.stat( pdfname ).st_mtime
            except FileNotFoundError:
                # ingen output er ikke nyere end nogen ting
                output_modtime = float('-inf')

            def gen_arg_list( args ):
                if not isinstance( args, tuple ):
                    args = args,
                if len(args) == 0:
                    return tuple()

                f, bookmark, verso = args + ( "", None, False )[len(args):]

                if type( f ) == str and f[-3:] == "pdf":
                    return ( f, bookmark, verso ),

                if type( f ).__name__ == "Revue":
                    return (
                        (
                            os.path.join(
                                self.conf["Paths"]["pdf"],
                                os.path.dirname( os.path.relpath( m.path )),
                                os.path.splitext( m.file_name )[0] + ".pdf"
                            ),
                            ( bookmark or m.title or None ),
                            verso )
                        for act in f.acts
                        for m in act.materials
                    )

                if type( f ).__name__ == "Actor":
                    return (
                        (
                            os.path.join(
                                self.conf["Paths"]["pdf"],
                                os.path.dirname(
                                    os.path.relpath( role.material.path )
                                ),
                                os.path.splitext(
                                    role.material.file_name
                                )[0] + ".pdf"
                            ),
                            ( bookmark or role.material.title or None ),
                            verso )
                        for role in f.roles
                    )

                # otherwise...
                print( f, bookmark, verso, args )
                raise TypeError("List must only contain PDF file paths, "
                                "a Revue object or an Actor object.")

            arg_list = [ arg for f in file_list for arg in gen_arg_list( f ) ]
            output.activity( os.getpid(), 1 )

            if not self.conf.getboolean( "TeXing", "force TeXing of all files" )\
               and not any( os.path.getmtime( f ) > output_modtime
                            for f,_,_ in arg_list ):
                output.skipped( os.getpid() )
                return              # intet nyt ind = intet nyt ud

            # så kører bussen
            writer = PdfWriter()
            writer.page_layout = "/TwoPageRight"
            writer.page_mode = "/UseOutlines"
            output.activity( os.getpid(), 1 )

            tex_translations = { "\\texttrademark": "™",
                                 "--": "–",
                                 "---": "—",
                                 "''": "“",
                                 "``": "”"
                                }
            for filename, bookmark, verso in arg_list:
                pagenum = len(writer.pages)
                if pagenum % 2 == 1 and not verso and\
                   self.conf.getboolean( "Collation",
                                         "insert blank back pages" ):
                    writer.add_blank_page()
                    pagenum += 1

                inpdf = PdfReader( filename )
                writer.append_pages_from_reader( inpdf )

                if bookmark:
                    for t in tex_translations:
                        bookmark = bookmark.replace( t, tex_translations[t] )

                    writer.add_outline_item( bookmark, pagenum )

                output.activity( os.getpid(), 1 )            

            with open(pdfname, "wb") as o:
                writer.write( o )
                o.close()
                output.activity( os.getpid(), 1 )

            try:
                pdfsizeopt = subprocess.Popen(
                    [ os.environ['PDFSIZEOPT'],
                      os.path.abspath( pdfname ),
                      os.path.abspath( pdfname ) ],
                    cwd = os.path.dirname( os.environ['PDFSIZEOPT'] ),
                    stdout = subprocess.PIPE,
                    stderr = subprocess.STDOUT,
                    text = True
                )
            except KeyError:
                # Environment variable not found
                pass
            else:
                while True:
                    o,e = "",""
                    try:
                        o,e = pdfsizeopt.communicate( timeout = 1 )
                    except subprocess.TimeoutExpired:
                        pass
                    else:
                        output.activity(
                            os.getpid(),
                            sum( 1 for c in o if c == '\n' )
                        )
                        # output loads and break things
                        if self.conf.getboolean( "TeXing", "verbose output" ):
                            print( o )
                    rc = pdfsizeopt.returncode
                    if rc == 0:
                        break
                    if rc != None:
                        raise subprocess.CalledProcessError(
                            returncode = rc,
                            cmd = pdfsizeopt.args,
                            output = o
                        )

            output.success( os.getpid() )
            return 1
        except:
            output.failed( os.getpid() )
            raise

    def _catcher( self, *args ):
        try:
            return self.pdfmerge( *args )
        except Exception as e:
            return e
    
    def parallel_pdfmerge(self, file_list):
        "Merge a list of lists of PDF files in parallel."

        #if type(file_list[0]) == str:
        #    # Each element is a file path.
        with Pool(processes = cpu_count()) as pool,\
             PoolOutputManager() as man:
            po = man.PoolOutput( cpu_count() )
            po.queue_add( *( Path( dst ).name for _,dst in file_list ) )
            result = pool.starmap_async(
                self._catcher,
                [ f + (po,) for f in file_list ]
            )
            while not result.ready():
                sleep( 1 )
                po.refresh()
            # po.clonk()
            print( result.get() )

