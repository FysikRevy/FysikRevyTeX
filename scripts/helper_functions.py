import shutil
import glob

def wildcard_copy(src, dst):
    for file in glob.glob(src):
        shutil.copy(file, dst)
