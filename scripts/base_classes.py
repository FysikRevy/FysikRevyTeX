from dataclasses import dataclass, field
from enum import IntEnum, auto

class Prop:
    def __init__(self, prop, responsible, description):
        self.prop = prop
        self.responsible = responsible
        self.description = description

    def __repr__(self):
        return "{} ({})".format(self.prop, self.responsible)

class Role:
    def __init__(self, abbreviation, name, role):
        self.abbreviation = abbreviation.strip()
        self.actor = name.strip()
        self.role = role.strip()
        self.material = None

    def __repr__(self):
        return "{} ({}): {}".format(self.role, self.abbreviation, self.actor)

    def add_material(self, material):
        "Add the Material of the sketch/song the role appears in."
        self.material = material

class Actor:
    class As( IntEnum ):
        ROLE = auto()
        INSTRUCTOR = auto()
        NINJA = auto()
        TASKED = auto()         # no point...?
    @dataclass
    class Appearance():
        scene: object
        doing: IntEnum
        
    def __init__(self, name):
        self.name = name
        self.is_in = []
        self.roles = []
        self.instructorships = []
        self.ninjamoves = []
        self.ninjatasks = []

    def __repr__(self):
        return "{}".format(self.name)

    def add_role(self, role):
        self.roles.append(role)
        self.is_in.append( self.Appearance( role.material, self.As.ROLE ) )

    def add_instructorship( self, instructorship ):
        self.instructorships.append( instructorship )
        self.is_in.append(
            self.Appearance( instructorship.material, self.As.INSTRUCTOR )
        )

    def add_ninjamove( self, ninja ):
        self.ninjamoves.append( ninja )
        self.is_in.append( self.Appearance( ninja.scene, self.As.NINJA ) )

    def add_ninjatask( self, task ):
        self.ninjatasks.append( task )

@dataclass
class NinjaMove:
    time: str
    destination: str
    ninjanames: list[ str ]
    scene: object = None

    def to_serializable( self ):
        return { 'tidspunkt': self.time,
                 'tilfra': self.destination,
                 'tildelt': [ n for n in self.ninjanames ]
                }

    @classmethod
    def from_deserialized( cls, deser ):
        return cls( deser[ 'tidspunkt' ],
                    deser[ 'tilfra' ],
                    deser[ 'tildelt' ]
                   )

    def tex_cmd( self ):
        return '\\move{{{}}}{{{}}}{{{}}}'.format(
            self.time,
            self.destination,
            ''.join([ '\\ninja{{{}}}'.format( n ) for n in self.ninjanames ])
        )

@dataclass
class NinjaPropData:
    hardness: str
    name: str
    drawing: str

class NinjaProp( NinjaPropData ):
    def __init__( self, hardness, name, drawing, moves ):
        NinjaPropData.__init__( self, hardness, name, drawing )
        self.moves = [ move if isinstance( move, NinjaMove )
                       else NinjaMove( *move )
                       for move in moves
                      ]

    def to_serializable( self ):
        ser = { 'navn': self.name,
                'flytninger': [ move.to_serializable() for move in self.moves ]
               }
        if self.drawing:
            ser[ 'tegning' ] = self.drawing
        if self.hardness:
            ser[ 'sværhed' ] = self.hardness
        return ser

    @classmethod
    def from_deserialized( cls, deser ):
        default_deser = deser | { 'tegning': '',
                                  'sværhed': ''
                                 }
        return cls( default_deser[ 'sværhed' ],
                    default_deser[ 'navn' ],
                    default_deser[ 'tegning' ],
                    [ NinjaMove.from_deserialized( move )
                      for move in default_deser[ 'flytninger' ]
                     ]
                   )

    def tex_cmd( self ):
        return [ '\\prop{{{}}}{{{}}}{{'.format( self.hardness, self.name ) ] \
            + ([ '  ' + self.drawing ] if self.drawing else []) \
            + [ '}{' ] \
            + [ '  ' + move.tex_cmd() for move in self.moves ] \
            + [ '}' ]

@dataclass
class NinjaTask():
    description: str
    ninjanames: list[ str ]
    scenes: list = field( default_factory = list )

    def tex_cmd( self ):
        return [ "\\tash{{{}}}{{{}}}".format(
            self.description,
            "".join("\\ninja{{{}}}".format( name ) for name in self.ninjanames)
        )]
