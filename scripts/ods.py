from collections import OrderedDict
import pyexcel_ods3 as ods
import os

from config import configuration as conf

try:
    fn = conf["Files"]["roles-summary"]
except KeyError:
    fn = "roles.ods"

class Ods:
    def __init__( self, fn = fn ):
        self.sheet = ods.get_data( fn )

    def import_revue_1( self, revue ):
        conv_revue = [["","Akt","Titel","Filnavn","Roller"]]
        for act in revue.acts:
            conv_act = []
            for mat in act.materials:
                roles = [
                    ['Fork.','','',''] \
                      + [ role.abbreviation for role in mat.roles ],
                    ['Skuespiller','','',''] \
                      + [ role.actor for role in mat.roles ],
                    ['Beskrivelse','','',''] \
                      + [ role.role for role in mat.roles ]
                ]
                roles[0][2] = mat.title
                roles[0][3] = os.path.relpath( mat.path )\
                                     .replace( os.path.sep, "/" )
                conv_act += roles
            conv_act[0][1] = act.name
            conv_revue += conv_act
        self.sheet["Aktoversigt"] = conv_revue

    def import_revue_2( self, revue ):
        blocks = []
        for act in revue.acts:
            act_blocks = []
            for mat in act.materials:
                mat_cells = [['','',''],
                             [ mat.title, '', '' ],
                             [ os.path.realpath( mat.path )\
                               .replace( os.path.sep, "/" ),\
                               "",""
                              ],
                             [ "Skuespiller","Fork.","Beskrivelse" ]
                            ]
                mat_cells += [ [ role.actor, role.abbreviation, role.role ]
                               for role in mat.roles ]
                act_blocks += [ mat_cells ]
            act_blocks[0][0][0] = act.name
            blocks += act_blocks
        bottom = max( *[ len( block ) for block in blocks ] )
        self.sheet["Aktoversigt"] = [
            [ cell
              for block in blocks
              for cell in ( block[n] if len(block) > n else ['','',''])
             ]
            for n in range(bottom)
        ]

    def write( self, fn = fn ):
        ods.save_data( fn, self.sheet )

    def write_csv( self, fn = 'roles.csv' ):
        with open( fn, "w" ) as f:
            f.write( "\n".join(
                [ ";".join(line) for line in self.sheet["Aktoversigt"] ]
            ) )
