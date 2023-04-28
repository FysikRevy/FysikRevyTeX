# coding=utf-8
from configparser import ConfigParser, ExtendedInterpolation
import os
import shutil
import subprocess
import sys
from time import localtime, strftime

sys.path.append("scripts")
import setup_functions as sf

if len(sys.argv) < 2:
    sys.exit("You must specify the directory to be created as an argument to this script. Exiting.")

# Get the destination directory (i.e. the one to be created):
dst_dir = os.path.abspath(sys.argv[1])
# Get the current working directory:
src_dir = os.getcwd()

# Try creating the directory:
try:
    os.mkdir(dst_dir)
except:
    sys.exit("Directory already exists. Please remove it and rerun this script. Exiting.")
    #print("\033[0;31mRemoving and recreating directory {} - be careful and remember to remove this feature before release!\033[0m".format(dst_dir))
    #shutil.rmtree(dst_dir)
    #os.mkdir(dst_dir)



# Ask for name and year:
revue_name = input("Enter revue name (enter for FysikRevy\\texttrademark): ")
revue_year = input("Enter year (enter for {}): ".format(strftime("%Y", localtime())))

if revue_name == "":
    revue_name = r"FysikRevy\texttrademark"
if revue_year == "":
    revue_year = strftime("%Y", localtime())



# Copy configuration:
with open(os.path.join(src_dir, "templates", "revytex.conf"), 'r', encoding='utf-8') as f:
    conf = f.read()
conf = conf.replace("REVUENAME", revue_name)
conf = conf.replace("REVUEYEAR", revue_year)

with open(os.path.join(dst_dir, "revytex.conf"), 'w', encoding='utf-8') as f:
    f.write(conf)

# Load the config file to get the correct directory names to be created:
conf = ConfigParser(interpolation=ExtendedInterpolation())
conf.read(os.path.join(dst_dir, "revytex.conf"))
paths = conf["Paths"]


# Create new directories:
os.mkdir(os.path.join(dst_dir, paths["pdf"]))
os.mkdir(os.path.join(dst_dir, paths["individual pdf"]))
os.mkdir(os.path.join(dst_dir, paths["songs"]))
os.mkdir(os.path.join(dst_dir, paths["sketches"]))
os.mkdir(os.path.join(dst_dir, paths["pdf"], paths["songs"]))
os.mkdir(os.path.join(dst_dir, paths["pdf"], paths["sketches"]))
os.mkdir(os.path.join(dst_dir, paths["templates"]))
os.mkdir(os.path.join(dst_dir, paths["cache"]))
os.mkdir(os.path.join(dst_dir, paths["pdf cache"]))

# Create templates:
sf.create_sketch_template(os.path.join(dst_dir, paths["templates"]), conf)
sf.create_song_template(os.path.join(dst_dir, paths["templates"]), conf)
# Copy templates to the right directories:
sf.wildcard_copy(os.path.join(src_dir, "templates", "*_template.tex"), 
                 os.path.join(dst_dir, paths["templates"]))
shutil.copy(os.path.join(src_dir, "templates", "contacts.csv"), 
            os.path.join(dst_dir, "contacts.csv"))

# Create symbolic links for system scripts and directories:
os.symlink(os.path.join(src_dir, "scripts"), os.path.join(dst_dir, paths["scripts"]), target_is_directory=True)
os.symlink(os.path.join(src_dir, "create.py"), os.path.join(dst_dir, "create.py"))
os.symlink(os.path.join(src_dir, "scripts", "revy.sty"), os.path.join(dst_dir, "revy.sty"))
os.symlink(os.path.join(src_dir, "scripts", "revy.sty"), os.path.join(dst_dir, paths["songs"], "revy.sty"))
os.symlink(os.path.join(src_dir, "scripts", "revy.sty"), os.path.join(dst_dir, paths["sketches"], "revy.sty"))


# Change to the new directory:
os.chdir(dst_dir)

### NOTE: The following is for testing only and should be removed!
#sf.wildcard_copy("/home/ks/documents/fysikrevy/jubilæumsrevy13/2013/sange/*.tex", "{}/sange/".format(dst_dir))
#sf.wildcard_copy("/home/ks/documents/fysikrevy/jubilæumsrevy13/2013/sketches/*.tex", "{}/sketches/".format(dst_dir))
#sf.wildcard_copy("/home/ks/documents/fysikrevy/jubilæumsrevy13/2013/sketches/*.jpg", "{}/sketches/".format(dst_dir))



print("\nCongratulations! FysikRevyTeX is now successfully set up and ready to run!")
print("""To get started, please do the following in the given order:
    1. Copy your TeX files to the right directories (e.g. songs in 'sange', sketches in 'sketches' etc.).
    2. Run 'python create.py plan' to automatically create the plan file.
    3. Edit the plan file by rearranging the files in the right order. Remember to also write the name of the act, e.g. "Akt 1".
    4. Take a look at revytex.conf and change any settings you want.
    5. Run 'python create.py' to create your first TeXhæfte.
    6. Rejoice!
    """)
