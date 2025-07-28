import os,sys

from pprint import pprint
from itertools import chain, dropwhile, islice

from more_itertools import stagger, intersperse

from prompt_toolkit import Application, ANSI, PromptSession
from prompt_toolkit.application import get_app
from prompt_toolkit.formatted_text import to_formatted_text, FormattedText
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, HorizontalAlign, ConditionalContainer, ScrollOffsets
from prompt_toolkit.layout.scrollable_pane import ScrollablePane
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_bindings import Binding
from prompt_toolkit.widgets import Label, Button
from prompt_toolkit.filters import has_focus, Never, Always
from prompt_toolkit.styles import Style, DynamicStyle, merge_styles

sys.path.append( os.getcwd() )
os.chdir( "E:/thebe/Git/revymanus2025/" )

from classy_revy import Revue, Scene
from tex import TeX
from clobberers import replace_ninjas

class FocusableLabel( Label ):
   def __init__( self, text = "", *args, **kwargs ):
      Label.__init__( self, text, *args, **kwargs )
      self.formatted_text_control.focusable = Always()

def formatted_control( text ):
   return FormattedText(
      (("italic", " [{}]".format(text) ),)
   )

r = Revue.fromfile("aktoversigt.plan")
items = [ m.title for m in r.materials ]

# items = ["one","two","three"]
# controls = [ control("w/r/n") for _ in items ]
number_style = Style.from_dict({"number": "ansibrightblack" })
def highlightable_number( index, of_number ):
   def style_number():
      try:
         n = get_app().number
      except (AttributeError, NameError):
         return number_style
      if index > len( n )\
            or len( str( of_number )) < len( n )\
            or str( of_number )[ : index + 1 ] != n[ : index + 1 ]:
         return number_style
      return None
   return DynamicStyle( style_number )

foci = { mat: FocusableLabel( formatted_control( "w/r/n" ) )
         for mat in r.materials
        }
controls = { mat: [ foci[ mat ] ] \
             + [ Label( formatted_control( t ), dont_extend_width=True )
                 for t in ( "↑", "↓" )
                ]
             for mat in r.materials
            }

numbers = { mat: FormattedText(
   # for the first digit in eg. 192, the class should be 1.19.192
   # this makes the class selectable when typing, say, 1 or 1-9, but not
   # when typing 1-8
   [( "class:number class:" \
      + ".".join( str( n + 1 )[ : j ]
                  for j in range( i + 1, len( str( n + 1)) + 1 ))
      , c
     )
    for i,c in enumerate( str( n + 1 ))
    ]) for n, mat in enumerate( r.materials ) }

def filter_for_control( idx ):
   if idx < 0:
      return Never()
   try:
      return has_focus( controls[idx][0] )
   except IndexError:
      return Never()

def neighbour_mats( mat ):
   return [ m for m in next(
      g for g in stagger( r.materials, offsets=(-1,0,1), longest=True )
      if isinstance( mat, Scene) and g[1] == mat\
      or isinstance( mat, Window ) and mat == foci[ g[1] ].window
   )]

def active_line( mat ):
   adjacent_mats = neighbour_mats( mat )
   return VSplit([
      Label( FormattedText([("",
                             ("  [" + " " * ( 2 - len( numbers[ mat ] )))
                             )])\
             + numbers[ mat ]\
             + FormattedText((
                ("", "] {} ".format( mat.title )),
                ("ansibrightblack", "(") ))\
             + FormattedText((
                ("ansibrightcyan", "{}:".format( len( mat.ninjaprops ) )),
                *intersperse( ("ansibrightblack", ","),
                              (( "ansibrightblack" if n == 0 \
                                 else "ansibrightgreen"
                                 , str( n )
                                ) for n in (
                                   sum( 1 for p in mat.ninjaprops
                                        if p.hardness == str(i)
                                       )
                                   for i in range( 1, 6 )
                                ))
                               ),
                *((("ansiyellow", " ({})".format(
                   sum( 1 for p in mat.ninjaprops
                        if p.hardness not in [ str(i) for i in range( 1,6 ) ]
                       ))),) if any( p.hardness not in
                                     [ str(i) for i in range( 1,6 ) ]
                                     for p in mat.ninjaprops
                                    ) \
                             else []
                  )) if mat.ninjaprops != None else (
                     ("ansibrightblack", " --- "),
                  )
                             )\
             + FormattedText((
                ("ansibrightblack", ")"),
                ("", " ")
             )),
             dont_extend_width = True
            )
   ] + [ ConditionalContainer( controls, filter )
         for controls, filter in zip(
               controls[ mat ],
               ( has_focus( foci[m] ) if m else Never()
                 for m in [ adjacent_mats[i] for i in ( 1,2,0 ) ]
                )
         )
        ]
                 )

def iterdex( element, iterator ):
   try:
      return next( i for i,e in enumerate( iterator ) if e == element )
   except StopIteration:
      raise ValueError( "Not found: {}".format( element ) )

all_windows = [ t for a in r.acts for t in
                [ Label( FormattedText( (("ansibrightblue bold",
                                          a.name + ":"
                                          ),)
                                       ))
                 ] \
                + [ active_line( m ) for m in a.materials ]
               ]

def prompt_windows( ninjaprops ):
   return [ Label( "\\ninjas{" ) ]\
      + [ Label( l ) for a in (
          ((( f"  \\prop{{{prop.hardness}}}{{{prop.name}}}{{",
              "    " + prop.drawing,
            "  }{"
             ),)\
          + tuple(( (f"    \\move{{{move.destination}}}{{{move.time}}}{{",
               "      " + " ".join( "\\ninja{{{}}}".format( name )
                                    for name in move.ninjanames
                                   ),
               "    }"
               )) for move in prop.moves
                  )\
           + tuple((( "  }",),),)) for prop in ninjaprops 
          ) for b in a for l in b
         ] + [ Label( "}" ) ]


kb = KeyBindings()
def wrapped_add( *keys, **kwargs ):
   def decorator( func ):
      @kb.add( *keys, **kwargs )
      def wrapped_handler( event ):
         event.app.number = ""
         func( event )
      return func
   return decorator
kb.wadd = wrapped_add

@kb.wadd('<any>')
def default_( event ):
   pass

@kb.wadd('q')
@kb.wadd('escape')
@kb.wadd('c-c')
def exit_(event):
   event.app.exit()

@kb.wadd('down')
def down_(event):
   adjacent_mats = neighbour_mats( event.app.layout.current_window )
   if adjacent_mats[2]:
      event.app.layout.focus( foci[ adjacent_mats[2] ] )

@kb.wadd('up')
def up_(event):
   adjacent_mats = neighbour_mats( event.app.layout.current_window )
   if adjacent_mats[0]:
      event.app.layout.focus( foci[ adjacent_mats[0] ] )

@kb.wadd('pagedown')
def pgdn_(event):
   *_, pageend = filter(
      lambda x: isinstance( x, Scene ),
      islice(
         dropwhile(
            lambda x: not isinstance( x, Scene ) \
                      or foci[x].window != event.app.layout.current_window,
            ( e for a in r.acts for e in
              chain((a,), ( m for m in a.materials ))
             )
         ),
         os.get_terminal_size().lines - 1 # interface-lines
      )
   )
   event.app.layout.focus( foci[ pageend ] )

@kb.wadd('pageup')
def pgup_(event):
   event.app.layout.focus( foci[
      next(
         m for m in next(
            g for g in stagger(
               ( e for a in r.acts
                 for e in chain( (a,), ( m for m in a.materials )) ),
               offsets = range( -os.get_terminal_size().lines + 2, 1 )
               #                           interface-lines + 1  ^
            )
            if isinstance( g[-1], Scene) \
               and foci[ g[-1] ].window == event.app.layout.current_window
         ) if isinstance( m, Scene )
      )
   ])

@kb.wadd('end')
def end_(event):
   *_, final = r.materials
   event.app.layout.focus( foci[ final ] )

@kb.wadd('home')
def home_(event):
   event.app.layout.focus( foci[ next( r.materials ) ] )

# for n in range(10):
#    @kb.add(str(n))
def number_func_for( n ):
   ns = str( n )
   def number_key_(event):
      try:
         event.app.number += ns
      except AttributeError:
         event.app.number = ns
      for _ in range(2):
         try:
            event.app.layout.focus( foci[
               next( mat for i,mat in enumerate( r.materials )
                     if str( i + 1 ).startswith( event.app.number )
                    )
            ])
            break
         except StopIteration:
            event.app.number = ns
   return number_key_

for n in range(10):
   kb.bindings.append( Binding( str( n ),
                                number_func_for( n )
                               ))

@kb.add('backspace')
def bs_(event):
   try:
      event.app.number = event.app.number[:-1]
   except:
      pass

def update_ninjas( event, new_ninjas ):
   mat = next( mat for mat in foci
               if foci[ mat ].window == event.app.layout.current_window
              )
   tex = TeX()
   tex.parse( mat.path )
   tex = replace_ninjas( tex, new_ninjas )
   tex.write( mat.path )
   tex.parse( mat.path )
   tex.info["path"] = mat.path
   mat.__init__( tex.info, print = lambda *args, **kwargs: None )
   menu_lines = event.app.layout.container.children[0].content.children
   menu_lines[ next( i for i,line in enumerate( menu_lines )
                     if event.app.layout.has_focus( line )
                    )
              ] = active_line( mat )

@kb.wadd('delete')
@kb.wadd('x')
def delete_( event ):
   update_ninjas( event, [""] )

@kb.wadd('n')
def new_( event ):
   update_ninjas( event, ["\\ninjas{}"] )

menu_layout = Layout(
   HSplit([
      ScrollablePane(
         HSplit( all_windows ),
         scroll_offsets = ScrollOffsets( top = 1, bottom = 1 )
      ),
      Button( "quit", lambda: get_app().exit() )
   ])
   , focused_element = foci[ next( r.materials ) ]
)

@kb.add('d')
def dt_(event):
   event.app.layout = Layout( ScrollablePane(
      HSplit( prompt_windows( next( r.materials ).ninjaprops
   ) ) ) )

# @kb.add('d')
# def lc_(event):
#    pprint( event.app.layout.get_visible_focusable_windows() )

@kb.add('i')
def invalidate_( event ):
   event.app.invalidate()

def highlight_number():
   try:
      n = get_app().number
   except:
      return None
   return Style.from_dict({
      # if n is eg. 192, should proeduce styles for 192, 19.192 and 1.19.192
      ".".join( n[ : j + 1 ] for j in range( i, len( n ))
               ): "ansiwhite underline"
      for i in range(len(n))
   }) if n else None

a = Application(
   key_bindings = kb,
   layout = menu_layout,
   # before_render = start_focusser,
   mouse_support = True,
   style = merge_styles([ Style.from_dict({"number": "ansibrightblack"})
                          , DynamicStyle( highlight_number )
                         ])
)

a.run()

