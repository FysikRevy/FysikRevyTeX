# builtins
from functools import reduce
from itertools import zip_longest
from pathlib import Path
from dataclasses import dataclass
from typing import Callable

# dependencies
from thefuzz import fuzz

# locals
from base_classes import Role
from classy_revy import Material, Revue
from helpers import rows_from_csv_etc

def trim_end( ar ):
    return reduce(
        lambda a,e: [e] + a if a or e else a,
        reversed( ar ),
        []
    )

def rowwise_csv( fn, revue ):
    """Det her er formatet, som create.py laver, når det får
argumentet roles-sheet. Men med den forskel, at overskrift-kolonnen er
valgfri. Rækkerne med ordantal bliver ignoreret, og behøver ikke at
være der. Kolonnen med aktnavne ignoreres, og behøver ikke at
udfyldes. For hvert nummer kan filnavn eller titel udelades. Hvis
begge er angivet prioriteres filnavnet.

    """

    materials = [ material for act in revue.acts for material in act.materials ]
    
    scorechart = {}
    translations = {}

    rows = rows_from_csv_etc( fn )
    row_gen = ( row for row in rows )
    title_col = 1 if\
        len( [ True for row in rows if not row[0] == '' ] ) / len( rows )\
        > 0.5 else 0

    def gather_mat( info_row ):
        title = info_row[ title_col + 1 ]
        fn = info_row[ title_col + 2 ]
        abbrs = trim_end( info_row[ title_col + 3 : ] )

        actor_row = next( row_gen )
        if any( actor_row[ title_col + 1 : title_col + 2 ] ):
            return gather_mat( actor_row )
        actors = trim_end( actor_row[ title_col + 3 : ] )

        instr_row = next( row_gen )
        if any (instr_row[ title_col + 1 : title_col + 2 ] ):
            return gather_mat( instr_row )
        if "nstruktør" in instr_row[0]:
            instrs = trim_end( instr_row[ title_col + 3 : ] )
            desc_row = next( row_gen )
        else:
            instrs = None
            desc_row = instr_row
            
        if any( desc_row[ title_col + 1 : title_col + 2 ] ):
            return gather_mat( desc_row )
        descs = trim_end( desc_row[ title_col + 3 : ] )

        role_info = {
            "roles": [ Role( abbr, actor, desc )
                       for abbr, actor, desc
                       in zip_longest( abbrs, actors, descs, fillvalue="" )
                      ]
        }
        try:
            role_info = {
                "instructors": [ Role( instr[0].lower(),
                                       actor,
                                       instr if instr != "i" else ""
                                      )
                                 for instr, actor
                                 in zip_longest( instrs, actors, fillvalue="" )
                                 if instr
                                ],
                "roles": [ role for role, instr
                           in zip( role_info["roles"], instrs )
                           if not instr or role.role
                          ] + role_info["roles"][ len(instrs) : ]
            }
        except TypeError:
            # no instrs
            pass
        
        if fn:
            translations[ title or fn ] = {
                "material": next(
                    ( mat for mat in materials
                      if Path( mat.path ).resolve() == Path( fn ).resolve()
                     ),
                    Material.fromfile( fn )
                ),
                "conf": "fn"   # or some actual signal...
            } | role_info
        else:
            scorechart[ title ] = {
                "scores": [ fuzz.partial_ratio( mat.title, title )
                            for mat in materials ]
            } | role_info

    try:
        while True:
            row = next( row_gen )
            if any( row[ title_col + 1 : title_col + 2 ] ):
                gather_mat( row )
    except StopIteration:
        pass

    fn_mats_indices = [ materials.index( translations[ title ][ "material" ] )
                        for title in translations ]
    for title in scorechart:
        for i in fn_mats_indices:
            scorechart[ title ][ "scores" ][ i ] = 0

    return { "translations": translations, "scorechart": scorechart }

def pdf_matrix( fname, revue ):
    try:
        rolenamerows = rows_from_csv_etc(
            revue.conf["Files"]["role_names"]
        )
        print("Bruger {} som rollenavneliste.\n".format(
            revue.conf["Files"]["role_names"]
        ))
    except FileNotFoundError:
        print(
            "Kunne ikke finde filen {}, "
            + "som er angivet i conf-filen.\n"
               .format( revue.conf["Files"]["role_names"] )
        )
    except KeyError:
        # not in conf
        pass
    else:
        rolenamedict = {}
        
        # skip to one after title line
        rows_iterator = ( row for row in rolenamerows )
        while True:
            title_row = next( rows_iterator )
            if not title_row[0]:
                break

        for row in rows_iterator:
            rolenames = {}
            for abbr, name in zip( title_row[1:], row[1:] ):
                if name:
                    rolenames[ abbr ] = name
            rolenamedict[ row[0] ] = rolenames

    # prøv at gætte sammenhængen mellem nummer-navne i
    # rollefordelingsfilen og manuskriptfilerne, med fuzzy
    # matching, se https://pypi.org/project/thefuzz/
    materials = [ material for act in revue.acts
                  for material in act.materials ]
    
    def rolename_when_exists( title, abbr ):
        try:
            return rolenamedict[ title ][ abbr ]
        except:
            return ""

    role_rows = ( row for row in rows_from_csv_etc( fname ) )

    instructor_abbrs = {}
    while True:
        preamble_row = next( role_rows )
        if not preamble_row[0]:
            title_row = preamble_row
            break
        if "=" in preamble_row[0]:
            abbr, desc = [ x.strip() for x in preamble_row[0].split( "=" ) ]
            instructor_abbrs[ abbr ] = desc
    
    scorechart = {
        row[0]: {
            "scores": [ fuzz.partial_ratio( material.title, row[0] )
                        for material in materials ],
            "roles": [ Role( abbr, name,
                             rolename_when_exists( row[0], abbr ) )
                       for abbr, name in zip( row[1:], title_row[1:] )
                       if abbr and abbr not in instructor_abbrs
                      ],
            "instructors": [ Role( abbr, name, instructor_abbrs[ abbr ] )
                             for abbr, name in zip( row[1:], title_row[1:] )
                             if abbr and abbr in instructor_abbrs
                            ] \
                           if instructor_abbrs else None
        }
        for row in role_rows
    }
    translations = {}
    return { "translations": translations, "scorechart": scorechart }

@dataclass
class RolesFormat:
    name: str
    description: str
    default_filename: str
    reader: Callable[[str, Revue], dict]

formats = [
    RolesFormat( name = "pdf-matrix",
                 default_filename = "roller.csv",
                 reader = pdf_matrix,
                 description = """\
Ligesom formatet i rolleoversigten, som bliver sat i manuskriptet."""
                ),
    RolesFormat( name = "overview",
                 default_filename = "roles.csv",
                 reader = rowwise_csv,
                 description = """\
Det format, som kommer ud af kommandoen roles-sheet til create."""
                )
]
