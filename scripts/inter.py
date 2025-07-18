import os,sys

from pprint import pprint
from itertools import chain, dropwhile, islice

from more_itertools import stagger

from prompt_toolkit import Application, ANSI
from prompt_toolkit.application import get_app
from prompt_toolkit.formatted_text import to_formatted_text, FormattedText
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, HorizontalAlign, ConditionalContainer, ScrollOffsets
from prompt_toolkit.layout.scrollable_pane import ScrollablePane
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import Label, Button
from prompt_toolkit.filters import has_focus, Never, Always

sys.path.append( os.getcwd() )
os.chdir( "E:/thebe/Git/revymanus2025/" )

from classy_revy import Revue, Scene

class FocusableLabel( Label ):
   def __init__( self, text = "", *args, **kwargs ):
      Label.__init__( self, text, *args, **kwargs )
      self.formatted_text_control.focusable = Always()

def formatted_control( text ):
   return FormattedText(
      (("ansibrightblack italic", " [{}]".format(text) ),)
   )

r = Revue.fromfile("aktoversigt.plan")
items = [ m.title for m in r.materials ]

# items = ["one","two","three"]
# controls = [ control("w/r/n") for _ in items ]

foci = { mat: FocusableLabel( formatted_control( "w/r/n" ) )
         for mat in r.materials
        }
controls = { mat: [ foci[ mat ] ] \
             + [ Label( formatted_control( t ) ) for t in ( "↑", "↓" ) ]
             for mat in r.materials
            }
numbers = { mat: [ ( c, "class:number" ) for c in str( n ) ]
            for n, mat in enumerate( r.materials )
           }

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

def active_line( text, mat ):
   adjacent_mats = neighbour_mats( mat )
   return VSplit([ Label( text=t, dont_extend_width=True )
                   for t in [ text, " " ] ]\
                 + [ ConditionalContainer( controls, filter )
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
                                       )
                         , dont_extend_width=True )
                 ] \
                + [ active_line( FormattedText((
                     ("", "  ["),
                     ("ansibrightblack", "{:>2}".format(
                        iterdex( m, r.materials ) + 1
                     )),
                     ("", "] " + m.title )
                    )), m ) for m in a.materials
                   ]
               ]

kb = KeyBindings()
def wrapped_add( *keys, filter = True ): # nevermind about the rest
   def decorator( func ):
      @kb.add( *keys, filter = filter )
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

@kb.add('9')
def one_(event):
   try:
      event.app.number += str( 9 )
   except AttributeError:
      event.app.number = str( 9 )
   for _ in range(2):
      try:
         event.app.layout.focus( foci[
            next( mat for i,mat in enumerate( r.materials )
                  if str( i + 1 ).startswith( event.app.number )
                 )
         ])
         return
      except StopIteration:
         event.app.number = str( 9 )

s = ScrollablePane( HSplit( all_windows ),
                    scroll_offsets = ScrollOffsets( top = 1, bottom = 1 )
                   )

@kb.add('d')
def dt_(event):
   print("ping")

# @kb.add('d')
# def lc_(event):
#    pprint( event.app.layout.get_visible_focusable_windows() )

a = Application(
   key_bindings = kb,
   layout = Layout( HSplit([ s,
                             Button( "quit", lambda: get_app().exit() )
                            ])
                    , focused_element = foci[ next( r.materials ) ]
                   ),
   # before_render = start_focusser,
   mouse_support = True,
   enable_page_navigation_bindings = True
)

a.run()


