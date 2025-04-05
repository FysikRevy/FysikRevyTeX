import os,re
from time import localtime, strftime
from datetime import timedelta
from locale import strxfrm

import base_classes as bc
from tex import TeX
from base_classes import Role
from converters import Converter

from config import configuration as conf
from pathlib import Path

re_m_s = [ re.compile( r"(\d[\d,.: ]*)[^\d]*" + word )
           for word in [ "inut", "ekund" ]
          ]

def extract_duration( eta, fn, property="eta" ):
    brok_if_absent_in = [ "eta" ]
    default_return = timedelta( 0 )
    def brok():
        print( "Unparsable {} ({}) in {}".format( property, eta, fn ) )
        return default_return

    e = eta.replace('$','').strip()
    if not e:
        if property in brok_if_absent_in:
            return brok()
        else:
            return default_return
    if ":" in e:
        m,s = e.split(":")
        try:
            return timedelta( minutes=int(m), seconds=int(s) )
        except ValueError:
            pass
    if "." in e or "," in e:
        try:
            return timedelta( minutes=float( e.replace( ",","." ) ) )
        except ValueError:
            pass
    m,s = [ (r.search( e ) or [ None, "0" ])[1] for r in re_m_s ]
    for t in m,s:
        if "." in t or "," in t or ":" in t:
            return extract_duration( t, fn, property )
    if not m == s == "0":
        return timedelta( minutes=int( m ), seconds=int(s) )
    try:
        return timedelta( minutes=int( e ) )
    except ValueError:
        return brok()

class Scene:
    "A Scene is a thing that (possibly) gets an entry in\n"\
    "the outline (aktoversigten)."
    # TODO: This class should perhaps inherit from the completely general
    # TeX class, as this is basically just a special case of a TeX file.
    # This would make functions easier, as they can treat TeX and
    # Material in the same way.
    @classmethod
    def fromstring( cls, string, source_file = None, source_mtime = None ):
        tex = TeX()
        re_cmd_start = re.compile( r"([^\n])\\" )
        tex.parse_lines( string if type( string ) == list
                         else re_cmd_start.sub( r"\1\n\\", string )\
                                .split( "\n" ) 
                        )
        return cls( tex.info, source_file, source_mtime )

    def __init__(self, info_dict, source_file = None, source_mtime = None ):
        "Extract data from dictionary returned by parsetexfile()."

        def info_dict_get_or_empty_string( entry ):
            # hvem ved, hvad de glemmer at skrive ind i tex-filen...
            try:
                return info_dict[ entry ]
            except KeyError:
                return ""

        try:
            self.file_name = source_file or self.file_name
        except AttributeError:
            # tried and failed to find self.file_name
            self.file_name = "generated TeX"
        
        self.title = info_dict_get_or_empty_string( "title" )
        try:
            self.shorttitle = info_dict["shorttitle"]
        except KeyError:
            #keep using the setter below
            pass

        self.status = info_dict_get_or_empty_string( "status" )
        if not self.status:
            print("No status on '{}' is set.".format(self.title))
        self.props = info_dict_get_or_empty_string( "props" )
        self.duration = extract_duration(
            info_dict_get_or_empty_string( "eta" ), self.file_name
        )
        self.length = str( self.duration // timedelta( minutes = 1 ) )\
            if self.duration else ""
        self.scenechange = extract_duration(
            info_dict_get_or_empty_string( "scenechange" ),
            self.file_name, "scenechange"
        )
        self.stage_roles = info_dict["roles"]
        self.instructors = info_dict["instructors"]
        self.responsible = info_dict_get_or_empty_string( "responsible" )
        if self.responsible not in [ role.actor for role in self.roles ]:
            print("Incorrect TeX responsible for '{}' ({})."
                  .format(self.title, self.responsible or "<unspecified>"))

        self.melody = info_dict_get_or_empty_string( "melody" )

        if source_mtime:
            self.modification_time = source_mtime

        # Save the file content:
        # TODO: even if there isn't a file...?
        self.tex = info_dict['tex']

        # Stuff that could be used for future features:
        self.appearing_roles = info_dict["appearing_roles"]
        # Like this:
        self.supernumeraries = [ role for role in self.appearing_roles
                                 if role not in [
                                    role.abbreviation for role in self.roles
                                 ]
        ]
        if conf.getboolean( "Role overview", "supernumeraries" )\
        and self.supernumeraries:
            self.roles += [ Role( " ".join( self.supernumeraries ),
                                  "!!!!!!!",
                                  ""
            )]

        self.category = info_dict_get_or_empty_string( "category" )

        # To be deprecated (most likely):
        self.author = info_dict_get_or_empty_string( "author" )
        if not self.author:
            print("No author for '{}' is declared.".format(self.title))
        self.year = info_dict_get_or_empty_string( "revyyear" )
        self.revue = info_dict_get_or_empty_string( "revyname" )
        self.version = info_dict_get_or_empty_string( "version" )

    @property
    def shorttitle( self ):
        try:
            return self._shorttitle
        except AttributeError:
            return self.title
    @shorttitle.setter
    def shorttitle( self, shorttitle ):
        self._shorttitle = shorttitle
    @shorttitle.deleter
    def shorttitle( self ):
        del self._shorttitle

    @property
    def shorttitle( self ):
        try:
            return self._shorttitle
        except AttributeError:
            return self.title
    @shorttitle.setter
    def shorttitle( self, shorttitle ):
        self._shorttitle = shorttitle
    @shorttitle.deleter
    def shorttitle( self ):
        del self._shorttitle

    @property
    def roles( self ):
        return self.stage_roles + self.instructors

    def __repr__(self):
        return "{} ({} min): {}".format(self.title, self.length, self.status)

    def register_actors(self, list_of_actors):
        "Takes a list of actors and updates it with the actors in the sketch/song."

        for role in self.roles:
            for actor in list_of_actors:
                if role.actor == actor.name:
                    # If the actor exists in the list, we add this role to him/her:
                    actor.add_role(role)
                    if role in self.instructors:
                        actor.add_instructorship( role )
                    break
            else:
                # If not, we create a new actor and update the list:
                actor = bc.Actor(role.actor)
                actor.add_role(role)
                if role in self.instructors:
                    actor.add_instructorship( role )
                list_of_actors.append(actor)


class Material( Scene ):
    "A Material is a Scene with an associated TeX file."
    
    @classmethod
    def fromfile(cls, filename):
        "Parse TeX file."
        tex = TeX()
        tex.parse(filename)
        info_dict = tex.info
        info_dict["path"] = filename
        return cls(info_dict)

    def __init__( self, info_dict ):
        
        self.path = os.path.abspath(info_dict["path"])
        path, self.file_name = os.path.split(self.path)

        super().__init__( info_dict )

        # Meta data
        self.modification_time = info_dict['modification_time']
        self.has_been_texed = False

        # Extract the category (which is the directory):
        self.category = Path( info_dict["path"] ).parts[0]

    def write(self, fname, encoding='utf-8'):
        "Write to a TeX file."
        # FIXME: this pretty much proves that TeX and Material need to be
        # merged somehow.
        with open(fname, 'w', encoding=encoding) as f:
            for line in self.tex:
                f.write(line)

    @property
    def wordcounts(self):
        try:
            return self._wordcounts
        except AttributeError:
            self._wordcounts = Converter().tex_to_wordcount( self.path )
            return self._wordcounts

    @wordcounts.setter
    def wordcounts( self, count ):
        self._wordcounts = count
            

class Act:
    def __init__(self):
        self.name = ""
        self.scenes = []

    def __repr__(self):
        desc = "{}: {} songs/sketches; {} min in total.\n".format(self.name, len(self.materials), self.get_length())
        for i,m in enumerate(self.scenes):
            desc += "  {}. {}\n".format(i+1, m)

        return desc

    def add_name(self, name):
        self.name = name

    def add_scene( self, new_scene ):
        self.scenes.append( new_scene )

    @property
    def materials( self ):
        return [ scene for scene in self.scenes
                 if isinstance( scene, Material )
                ]

    add_material = add_scene

    def is_empty(self):
        return len(self.materials) == 0

    def get_length(self, include_stubs = True ):
        t = 0
        n = {}
        scene_list = self.scenes if include_stubs else self.materials
        for m in scene_list:
            try:
                t += float(m.length)
            except ValueError:
                try:
                    n[m.length] += 1
                except KeyError:
                    n[m.length] = 1

        l = "{:4.2f}".format(t)
        for key in n:
            if n[key] != 1:
                l += " + {}{}".format(n[key],key)
            else:
                l += " + {}".format(key)

        return l



class Revue:
    def __init__(self, acts):
        self.acts = acts
        self.actors = []

        # Load variables from the configuration:
        # FIXME: Maybe just pass the ConfigParser object itself? There shouldn't
        # be a reason to reparse the file.
        self.conf = conf
        self.name = self.conf["Revue info"]["revue name"]
        self.year = self.conf["Revue info"]["revue year"]

        # Make a list of all actors:
        for material in self.materials:
            material.register_actors(self.actors)
        self.actors.sort(key=lambda actor: strxfrm(actor.name))


    @classmethod
    def fromfile(cls, filename, encoding='utf-8'):
        "Takes a plan file and extracts the information for each material."

        # Hust modifikations-tid for aktoversigten
        modification_time = os.stat( filename ).st_mtime

        re_tex_cmd = re.compile( r"\\\w+[[{]" )
        acts = []
        act = Act()

        with open(filename, mode='r', encoding=encoding) as f:
            for line in f.readlines():
                line = line.rstrip()
                if len(line) == 0 or line[0] == "#":
                    continue
                s = None
                if line[-4:] == '.tex':
                    s = Material.fromfile( line )
                elif re_tex_cmd.search( line ):
                    # stub scene
                    s = Scene.fromstring( line,
                                          Path( filename ).name,
                                          modification_time
                                         )
                if s:
                    for role in s.roles:
                        role.add_material(s)
                    act.add_scene(s)
                    continue
                    
                # otherwise, it must be the name of the new act:
                if act.is_empty():
                    # If the Act is empty, we give it a name:
                    act.add_name(line)
                else:
                    # If not, we store the current act and create a new:
                    acts.append(act)
                    act = Act()
                    act.add_name(line)
        
            # Store the very last act:
            acts.append(act)

        r = cls(acts)
        r.modification_time = modification_time
        return r

    def __repr__(self):
        acts = "{}".format(self.acts[0])
        for i in range(1,len(self.acts)):
            acts = "{}\n{}".format(acts, self.acts[i])

        return acts

    @property
    def materials( self ):
        return ( mat for act in self.acts for mat in act.materials )

    @property
    def scenes( self ):
        return ( sc for act in self.acts for sc in act.scenes )

    def write_roles_csv( self, fn = "roles.csv" ):
        fn = Path( fn )
        sep_car = "\t" if fn.suffix == ".tsv" else ";"
        table = [["","Akt","Titel","Filnavn","Roller"]]
        for act in self.acts:
            act_table = []
            for mat in act.materials:
                wordcount_overlap = []
                for role in mat.roles:
                    try:
                        role.sung = mat.wordcounts[ role.abbreviation ]["sung"]
                        role.spoken = mat.wordcounts[ role.abbreviation ]["spoken"]
                    except KeyError:
                        role.sung = ""
                        role.spoken = ""
                    wordcount_overlap += [ role.abbreviation ]
                    
                act_table += [
                    ['Fork.', '', mat.title,
                     Path( mat.path )\
                           .relative_to( Path.cwd(),  )\
                           .as_posix()
                     ] + [ role.abbreviation for role in mat.roles ]\
                       + [ abbr for abbr in mat.wordcounts
                           if abbr not in wordcount_overlap ],
                    ['Skuespiller','','','']\
                     + [ role.actor for role in mat.roles ],
                    ['Instruktørrolle','','','']\
                     + [ role.role or "i" if role in mat.instructors else ""
                         for role in mat.roles
                        ],
                    ['Beskrivelse','','','']\
                     + [ role.role if role in mat.stage_roles else ""
                         for role in mat.roles
                        ],
                    ['Ord i sange','','','']\
                     + [ role.sung for role in mat.roles ]\
                     + [ mat.wordcounts[ abbr ]["sung"]
                         for abbr in mat.wordcounts
                         if not any( abbr in o and abbr != o
                                     for o in wordcount_overlap
                                    )
                        ],
                    ['Ord i replikker','','','']\
                     + [ role.spoken for role in mat.roles ]\
                     + [ mat.wordcounts[ abbr ]["spoken"] for abbr in mat.wordcounts
                         if abbr not in wordcount_overlap ]
                ]
            act_table[0][1] = act.name
            table += act_table
        with fn.open( mode="w", encoding="utf-8" ) as f:
            f.write( "\n".join( [ sep_car.join(
                [ '"{}"'.format( cell ) if sep_car in str(cell)
                  else str(cell) if cell else ''
                  for cell in row
                 ] ) for row in table ] ) )
