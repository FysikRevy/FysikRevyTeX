import os
import sys

def create_sketch_template(dir, config):
    with open("templates/sketchskabelon.tex", 'r') as f:
        tex = f.read()

    tex = tex.replace("REVUENAME", config["Revue info"]["revue name"])
    tex = tex.replace("REVUEYEAR", config["Revue info"]["revue year"])

    with open("{}/sketchskabelon.tex".format(dir), 'w') as f:
        f.write(tex)


def create_song_template(dir, config):
    with open("templates/sangskabelon.tex", 'r') as f:
        tex = f.read()

    tex = tex.replace("REVUENAME", config["Revue info"]["revue name"])
    tex = tex.replace("REVUEYEAR", config["Revue info"]["revue year"])

    with open("{}/sangskabelon.tex".format(dir), 'w') as f:
        f.write(tex)


def create_plan_file(fname):
    if os.path.isfile(fname):
        choice = input("{} already exists. Remove it and create a new plan? y/[n]".format(fname))

        if choice == "n" or choice == "":
            sys.exit("Nothing to be done. Exiting.")

    songs = sorted(os.listdir("sange"), key=str.lower)
    sketches = sorted(os.listdir("sketches"), key=str.lower)

    with open(fname, 'w') as f:
        f.write("Sange\n")
        for song in songs:
            if song[-3:] == "tex":
                f.write("sange/{}\n".format(song))

        f.write("\nSketches\n")
        for sketch in sketches:
            if sketch[-3:] == "tex":
                f.write("sketches/{}\n".format(sketch))

