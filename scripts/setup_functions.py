import glob
import os
import shutil
import sys
from glob import glob

def wildcard_copy(src, dst):
    "Helper function easy setup of test environment. Only used in setup.py."
    for file in glob.glob(src):
        shutil.copy(file, dst)


def create_material_template(dir, texfile, config, encoding='utf-8'):
    with open(os.path.join(config["Paths"]["templates"], texfile), 'r', encoding=encoding) as f:
        tex = f.read()

    tex = tex.replace("<+REVUENAME+>", config["Revue info"]["revue name"])
    tex = tex.replace("<+REVUEYEAR+>", config["Revue info"]["revue year"])

    with open(os.path.join(dir, texfile), 'w', encoding=encoding) as f:
        f.write(tex)


def create_sketch_template(dir, config, encoding='utf-8'):
    create_material_template(dir, "sketchskabelon.tex", config)


def create_song_template(dir, config, encoding='utf-8'):
    create_material_template(dir, "sangskabelon.tex", config)

def tex_files_under_dir( dir ):
    # https://stackoverflow.com/questions/18394147/recursive-sub-folder-search-and-return-files-in-a-list-python#18394205
    return [y for x in os.walk( dir ) for y in glob( os.path.join( x[0], '*.tex'))]

def create_plan_file(fname, encoding='utf-8'):
    if os.path.isfile(fname):
        choice = input("{} already exists. Remove it and create a new plan? y/[n]".format(fname))

        if choice == "n" or choice == "":
            sys.exit("Nothing to be done. Exiting.")

    songs = sorted( tex_files_under_dir( "sange" ), key=str.lower)
    sketches = sorted( tex_files_under_dir( "sketches" ), key=str.lower)

    with open(fname, 'w', encoding=encoding) as f:
        f.write("Sange\n")
        for song in songs:
            if song[-3:] == "tex":
                f.write(os.path.join("sange", "{}\n".format(song)))

        f.write("\nSketches\n")
        for sketch in sketches:
            if sketch[-3:] == "tex":
                f.write(os.path.join("sketches", "{}\n".format(sketch)))

