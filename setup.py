from configparser import ConfigParser
import os
import shutil
import subprocess
import sys
from time import gmtime, strftime

sys.path.append("scripts/")
from helper_functions import wildcard_copy
import setup_functions as sf

if len(sys.argv) < 2:
    sys.exit("You must specify the directory to be created as an argument to this script. Exiting.")

# Get the destination directory (i.e. the one to be created):
dst_dir = os.path.abspath(sys.argv[1])
# Get the current working directory:
src_dir = os.getcwd()

# Setting up configuration:
config = ConfigParser()
config["Frontpage"] = {"version": "0011000100110000",
                       "top quote": r"Per Hedegård $\neq$ Baconost",
                       "bottom quote": "``Hvis ikke jeg havde haft den ugentlige dosis Rage Against the Machine på Caféen?, var jeg nok aldrig blevet prodekan''"}
config["Revue info"] = {}

# Try creating the directory:
try:
    os.mkdir(dst_dir)
except:
    #sys.exit("Directory already exists. Please remove it and rerun this script. Exiting.")
    print("\033[0;31mRemoving and recreating directory {} - be careful and remember to remove this feature before release!\033[0m".format(dst_dir))
    shutil.rmtree(dst_dir)
    os.mkdir(dst_dir)


# Add to config:
config["Revue info"]["revue name"] = input("Enter revue name (enter for FysikRevy\\texttrademark): ")
config["Revue info"]["revue year"] = input("Enter year (enter for {}): ".format(strftime("%Y", gmtime())))

if config["Revue info"]["revue name"] == "":
    config["Revue info"]["revue name"] = r"FysikRevy\texttrademark"
if config["Revue info"]["revue year"] == "":
    config["Revue info"]["revue year"] = strftime("%Y", gmtime())

# Create new directories:
os.mkdir("{}/pdf".format(dst_dir))
os.mkdir("{}/pdf/individuals".format(dst_dir))
os.mkdir("{}/sange".format(dst_dir))
os.mkdir("{}/sketches".format(dst_dir))
os.mkdir("{}/templates".format(dst_dir))

# Create templates:
sf.create_sketch_template("{}/templates".format(dst_dir), config)
sf.create_song_template("{}/templates".format(dst_dir), config)

# Create symbolic links for system scripts and directories:
os.symlink("{}/scripts".format(src_dir), "{}/scripts".format(dst_dir), target_is_directory=True)
os.symlink("{}/create.py".format(src_dir), "{}/create.py".format(dst_dir))
os.symlink("{}/scripts/revy.sty".format(src_dir), "{}/revy.sty".format(dst_dir))
os.symlink("{}/scripts/revy.sty".format(src_dir), "{}/sange/revy.sty".format(dst_dir))
os.symlink("{}/scripts/revy.sty".format(src_dir), "{}/sketches/revy.sty".format(dst_dir))


# Change to the new directory:
os.chdir(dst_dir)

### NOTE: The following is for testing only and should be removed!
wildcard_copy("/home/ks/documents/fysikrevy/jubilæumsrevy13/2013/sange/*.tex", "{}/sange/".format(dst_dir))
wildcard_copy("/home/ks/documents/fysikrevy/jubilæumsrevy13/2013/sketches/*.tex", "{}/sketches/".format(dst_dir))
wildcard_copy("/home/ks/documents/fysikrevy/jubilæumsrevy13/2013/sketches/*.jpg", "{}/sketches/".format(dst_dir))
##shutil.copytree("test_files/sange", "{}/sange".format(dst_dir))
##shutil.copytree("test_files/sketches", "{}/sketches".format(dst_dir))
#shutil.copy("test_files/aktoversigt.plan", "{}/aktoversigt.plan".format(dst_dir))

with open("revytex.conf", 'w') as configfile:
    config.write(configfile)


print("\nCongratulations! FysikRevyTeX is now successfully set up and ready to run!")
print("""To get started, please do the following in the given order:
    1. Copy your TeX files to the right directories (e.g. songs in 'sange', sketches in 'sketches' etc.).
    2. Run 'python create.py plan' to automatically create the plan file.
    3. Edit the plan file by rearranging the files in the right order. Remember to also write the name of the act, e.g. "Akt 1".
    4. Take a look at revytex.conf and change any settings you want.
    5. Run 'python create.py' to create your first TeXhæfte.
    6. Rejoice!
    """)
