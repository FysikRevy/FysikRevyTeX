import glob
import os
import shutil
import subprocess
import tempfile
import uuid
from multiprocessing import Pool, cpu_count

from PyPDF2 import PdfFileMerger

def wildcard_copy(src, dst):
    for file in glob.glob(src):
        shutil.copy(file, dst)


def generate_pdf(pdfname, tex, repetitions=2, encoding='utf-8'):
    "Generates a pdf from a TeX string."

    current_dir = os.getcwd()
    temp = tempfile.mkdtemp()
    os.chdir(temp)
    os.symlink(os.path.join(current_dir,"revy.sty"), "revy.sty")

    tempname = uuid.uuid4() 
    texfile = "{}.tex".format(tempname)
    pdffile = "{}.pdf".format(tempname)

    with open(texfile, 'w', encoding=encoding) as f:
        f.write(tex)

    for i in range(repetitions):
        #rc = subprocess.call(["pdflatex", "-halt-on-error", texfile])
        rc = subprocess.call(["pdflatex", "-halt-on-error", texfile], stdout=subprocess.DEVNULL)

    if rc == 0:
        print("{}: Success!".format(pdfname))
    else:
        print("{}: Failed!".format(pdfname))

    os.rename(pdffile, pdfname)
    shutil.copy(pdfname, os.path.join(current_dir,"pdf"))
    os.chdir(current_dir)
    shutil.rmtree(temp)


def generate_pdf_from_file(fname, repetitions=2):
    "Generates a pdf from a TeX file."

    path, filename = os.path.split(fname)
    pdfname = "{}.pdf".format(filename[:-4])

    current_dir = os.getcwd()
    os.chdir(path)

    for i in range(repetitions):
        #rc = subprocess.call(["pdflatex", "-halt-on-error", filename])
        rc = subprocess.call(["pdflatex", "-halt-on-error", filename], stdout=subprocess.DEVNULL)
        
    if rc == 0:
        print("{}: Success!".format(pdfname))
    else:
        print("{}: Failed!".format(pdfname))

    os.remove("{}.log".format(filename[:-4]))
    os.remove("{}.aux".format(filename[:-4]))
    os.chdir(current_dir)


def generate_multiple_pdfs(file_list, repetitions=2):
    "Generate multiple pdfs in parallel."

    if type(file_list[0]) == str:
        # Each element is a file path.
        with Pool(processes = cpu_count()) as pool:
            result = pool.map(generate_pdf_from_file, file_list)


def merge_pdfs(file_list, pdfname):
    merger = PdfFileMerger()

    for f in file_list:
        if type(f) == str:
            fo = open(f, "rb")
            merger.append(fileobj = fo)

        elif type(f).__name__ == "Revue":
            for act in f.acts:
                for m in act.materials:
                    merger.append(os.path.join(m.category, "{}.pdf".format(m.file_name[:-4])))
        
        elif type(f).__name__ == "Actor":
            print(f.name)
            for role in f.roles:
                merger.append(os.path.join(role.material.category, "{}.pdf".format(role.material.file_name[:-4])))


    output = open(pdfname, "wb")
    merger.write(output)

        
