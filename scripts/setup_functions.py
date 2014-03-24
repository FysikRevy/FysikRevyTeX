import os
import sys

def create_sketch_template(dir, config, encoding='utf-8'):
    with open(os.path.join(config["Paths"]["templates"], "sketchskabelon.tex"), 'r', encoding=encoding) as f:
        tex = f.read()

    tex = tex.replace("REVUENAME", config["Revue info"]["revue name"])
    tex = tex.replace("REVUEYEAR", config["Revue info"]["revue year"])

    with open(os.path.join(dir, "sketchskabelon.tex"), 'w', encoding=encoding) as f:
        f.write(tex)


def create_song_template(dir, config, encoding='utf-8'):
    with open(os.path.join(config["Paths"]["templates"], "sangskabelon.tex"), 'r', encoding=encoding) as f:
        tex = f.read()

    tex = tex.replace("REVUENAME", config["Revue info"]["revue name"])
    tex = tex.replace("REVUEYEAR", config["Revue info"]["revue year"])

    with open(os.path.join(dir, "sangskabelon.tex"), 'w', encoding=encoding) as f:
        f.write(tex)


def create_plan_file(fname, encoding='utf-8'):
    if os.path.isfile(fname):
        choice = input("{} already exists. Remove it and create a new plan? y/[n]".format(fname))

        if choice == "n" or choice == "":
            sys.exit("Nothing to be done. Exiting.")

    songs = sorted(os.listdir("sange"), key=str.lower)
    sketches = sorted(os.listdir("sketches"), key=str.lower)

    with open(fname, 'w', encoding=encoding) as f:
        f.write("Sange\n")
        for song in songs:
            if song[-3:] == "tex":
                f.write(os.path.join("sange", "{}\n".format(song)))

        f.write("\nSketches\n")
        for sketch in sketches:
            if sketch[-3:] == "tex":
                f.write(os.path.join("sketches", "{}\n".format(sketch)))

