#import subprocess
import os
from multiprocessing import Pool, cpu_count

from PyPDF2 import PdfFileMerger

import config as cf

conf = cf.Config()

class PDF:
    def __init__(self):
        self.conf = conf

    def pdfmerge(self, file_list, pdfname):
        "Merge a list of PDF files."

        merger = PdfFileMerger()

        for f in file_list:
            if type(f) == str and f[-3:] == 'pdf':
                fo = open(f, "rb")
                merger.append(fileobj = fo)

            elif type(f).__name__ == "Revue":
                for act in f.acts:
                    for m in act.materials:
                        merger.append(os.path.join(self.conf["Paths"]["pdf"],
                            m.category, 
                            "{}.pdf".format(m.file_name[:-4])))
            
            elif type(f).__name__ == "Actor":
                for role in f.roles:
                    merger.append(os.path.join(self.conf["Paths"]["pdf"],
                        role.material.category, 
                        "{}.pdf".format(role.material.file_name[:-4])))

            else:
                raise TypeError("List must only contain PDF file paths, "
                                "a Revue object or an Actor object.")

        try:
            output = open(pdfname, "wb")
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

