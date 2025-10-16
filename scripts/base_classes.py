from dataclasses import dataclass

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
    def __init__(self, name):
        self.name = name
        self.roles = []
        self.instructorships = []
        self.ninjamoves = []

    def __repr__(self):
        return "{}".format(self.name)

    def add_role(self, role):
        self.roles.append(role)

    def add_instructorship( self, instructorship ):
        self.instructorships.append( instructorship )

    def add_ninjamove( self, ninja ):
        self.ninjamoves.append( ninja )

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
