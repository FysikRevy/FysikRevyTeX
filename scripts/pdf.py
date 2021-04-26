#import subprocess
import os
from multiprocessing import Pool, cpu_count

from PyPDF2 import PdfFileMerger

from config import configuration as conf

class PDF:
    def __init__(self):
        self.conf = conf

    def pdfmerge(self, *args, **kwargs):
        "Dummy wrapper to make multiprocessing work."
        return self._pdfmerge(*args, **kwargs)

    def _pdfmerge(self, file_list, pdfname):
        """Merge a list of PDF files.  
file_list kan være en liste med filnavne, eller en liste med tupler af
filnavne og bogmærkenavne (til indholdsfortegnelsen)."""
        # det er egentlig noget hø, sådan automagisk at bøje sig rundt
        # om forskellige typer i argumenterne. Det nærmest tigger og
        # be'r om at blive til en bug i fremtiden. Men det giver
        # mening som et format, og bagudkompatibilitet er vigtigt. Så
        # nu er vi her.

        # check, om output er nyere end input
        try:
            output_modtime = os.stat( pdfname ).st_mtime
        except FileNotFoundError:
            # ingen output er ikke nyere end nogen ting
            output_modtime = float('-inf')

        merge_args = ()         # argumenter til PyPDF2 append()
        found_fresh_input = False # flag (::sadface::)

        for f in file_list:
            if type(f) == str and f[-3:] == 'pdf':
                merge_args += ({ "fileobj": f,
                                },)
                found_fresh_input |= (
                    os.stat( f ).st_mtime > output_modtime
                )

            elif type(f).__name__ == "Revue":
                for act in f.acts:
                    for m in act.materials:
                        pdfpath = os.path.join(
                            self.conf["Paths"]["pdf"],
                            os.path.dirname( os.path.relpath( m.path )),
                            os.path.splitext( m.file_name )[0] + ".pdf"
                        )
                        merge_args += ({
                            "fileobj": pdfpath,
                        },)
                        found_fresh_input |= (
                            os.path.getmtime( pdfpath ) > output_modtime
                        )                        
            
            elif type(f).__name__ == "Actor":
                for role in f.roles:
                    pdfpath = os.path.join(
                        self.conf["Paths"]["pdf"],
                        os.path.dirname( os.path.relpath( role.material.path )),
                        os.path.splitext( role.material.file_name )[0] + ".pdf"
                    )                    
                    merge_args += ({
                        "fileobj": pdfpath,
                    },)
                    found_fresh_input |= (
                        os.path.getmtime( pdfpath ) > output_modtime
                    )                        

            else:
                raise TypeError("List must only contain PDF file paths, "
                                "a Revue object or an Actor object.")

        if ( not found_fresh_input
             and not self.conf.getboolean(
                 "TeXing", "force TeXing of all files"
             )
            ):
            return              # intet nyt ind = intet nyt ud

        merger = PdfFileMerger()

        # så kører bussen
        for kwargs in merge_args:
            merger.append( **kwargs )

        try:
            with open(pdfname, "wb") as output:
                merger.write(output)
                output.close()
        except FileNotFoundError:
            err = "File could not be opened: {}".format(pdfname)
            rc = 1
        except:
            rc = 1
        else:
            rc = 0

        print("{:<42}".format("\033[0;37;1m{}:\033[0m".format(os.path.split(pdfname)[1])), end="")
        if rc == 0:
            print("\033[0;32m Success!\033[0m")
        else:
            print("\033[0;31m Failed!\033[0m")
            print("  -> {}".format(err))
        

    
    def parallel_pdfmerge(self, file_list):
        "Merge a list of lists of PDF files in parallel."

        #if type(file_list[0]) == str:
        #    # Each element is a file path.
        with Pool(processes = cpu_count()) as pool:
            result = pool.starmap(self.pdfmerge, file_list)

