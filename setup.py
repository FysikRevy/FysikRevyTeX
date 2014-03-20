import json
import os
import shutil
import subprocess
import sys
from time import gmtime, strftime

sys.path.append("scripts/")
from helper_functions import wildcard_copy

if len(sys.argv) < 2:
    sys.exit("You must specify the directory to be created as an argument to this script. Exiting.")

config = {}
src_dir = os.getcwd()

try:
    os.mkdir(sys.argv[1])
except:
    #sys.exit("Directory already exists. Please remove it and rerun this script. Exiting.")
    print("\033[0;31mRemoving and recreating directory {} - be careful and remember to remove this feature before release!\033[0m".format(sys.argv[1]))
    shutil.rmtree(sys.argv[1])
    os.mkdir(sys.argv[1])

config["revue_name"] = input("Enter revue name (enter for FysikRevy\\texttrademark): ")
config["revue_year"] = input("Enter year (enter for {}): ".format(strftime("%Y", gmtime())))

if config["revue_name"] == "":
    config["revue_name"] = r"FysikRevy\texttrademark"
if config["revue_year"] == "":
    config["revue_year"] = strftime("%Y", gmtime())

os.symlink("{}/templates".format(src_dir), "{}/templates".format(sys.argv[1]), target_is_directory=True)
os.symlink("{}/scripts".format(src_dir), "{}/scripts".format(sys.argv[1]), target_is_directory=True)
os.symlink("{}/create.py".format(src_dir), "{}/create.py".format(sys.argv[1]))
os.symlink("{}/scripts/revy.sty".format(src_dir), "{}/revy.sty".format(sys.argv[1]))
os.symlink("{}/scripts/revy.sty".format(src_dir), "{}/sange/revy.sty".format(sys.argv[1]))
os.symlink("{}/scripts/revy.sty".format(src_dir), "{}/sketches/revy.sty".format(sys.argv[1]))

## NOTE: The following is for testing only and should be removed!
os.mkdir("{}/sange".format(sys.argv[1]))
os.mkdir("{}/sketches".format(sys.argv[1]))
wildcard_copy("test_files/sange/*.tex", "{}/sange/".format(sys.argv[1]))
wildcard_copy("test_files/sketches/*.tex", "{}/sketches/".format(sys.argv[1]))
#shutil.copytree("test_files/sange", "{}/sange".format(sys.argv[1]))
#shutil.copytree("test_files/sketches", "{}/sketches".format(sys.argv[1]))
shutil.copy("test_files/aktoversigt.plan", "{}/aktoversigt.plan".format(sys.argv[1]))

os.chdir(sys.argv[1])
os.mkdir("pdf")

with open(".config.json", 'w') as f:
    json.dump(config, f, sort_keys=True, indent=4, separators=(',', ': '))
