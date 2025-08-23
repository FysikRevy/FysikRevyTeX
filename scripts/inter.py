import os,sys

from pprint import pprint
from itertools import chain, dropwhile, islice
from copy import copy

from more_itertools import stagger, intersperse

from prompt_toolkit import Application, ANSI, PromptSession
from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.application import get_app
from prompt_toolkit.formatted_text import to_formatted_text, FormattedText, fragment_list_len
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, HorizontalAlign, VerticalAlign, ConditionalContainer, ScrollOffsets, FloatContainer, Float
from prompt_toolkit.layout.scrollable_pane import ScrollablePane
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.processors import AfterInput, Processor, explode_text_fragments, Transformation
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import Binding
from prompt_toolkit.widgets import Label, Button, TextArea
from prompt_toolkit.filters import has_focus, Never, Always, is_true, Condition, to_filter
from prompt_toolkit.styles import Style, DynamicStyle, merge_styles
from prompt_toolkit.output import Output

sys.path.append( os.getcwd() )
os.chdir( "E:/thebe/Git/revymanus2025/" )

from classy_revy import Revue, Scene
from base_classes import NinjaProp
from tex import TeX
from clobberers import replace_ninjas

class FocusableLabel( Label ):
   def __init__( self, text = "", *args, **kwargs ):
      Label.__init__( self, text, *args, **kwargs )
      self.formatted_text_control.focusable = Always()

class NarrowLabel( Label ):
   def __init__( self, *args, **kwargs ):
      if len(args) >= 4 or "dont_extend_width" in kwargs:
         return Label.__init__( self, *args, **kwargs )
      return Label.__init__( self, *args, dont_extend_width=True, **kwargs )

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

testprops = next( islice( r.materials, 1, None ) ).props
@kb.add('d')
def dt_(event):
   pprint( [ p.prop for p in testprops ] )

@kb.add('i')
def inv_(event):
   event.app.invalidate()

nav_kb = KeyBindings()
@nav_kb.add('up')
def up_(event):
   event.app.layout.focus_previous()
@nav_kb.add('down')
def down_(event):
   event.app.layout.focus_next()

class TextAreaWithBindings( TextArea ):
   def __init__( self, *args, **kwargs ):
      TextArea.__init__( self, *args, **kwargs )
      self.control.key_bindings = merge_key_bindings((
         load_key_bindings(), nav_kb
      ))

class NinjasLine(TextArea):
   def __init__( self, ninjas ):
      try:
         # the final space is where the command to add a ninja is active.
         # but if there are no ninjas, the final space is the *only* space.
         # don't forget that it's there.
         ninjas = ninjas[:-1] + [ ninjas[-1] + " " ]
      except IndexError:
         pass
      
      class ClotheNinjas(Processor):
         def apply_transformation( self, trans_input ):
            if not trans_input.document.text:
               return Transformation( trans_input.fragments )
            
            inter = FormattedText([ ("", " } "),
                                    ("ansicyan", "\\ninja"),
                                    ("", "{ ")
                                   ])
            trans_fragments = (
               frag for frag in explode_text_fragments( trans_input.fragments )
            )
            fragments = [
               frag for frag in islice( trans_fragments,
                                        trans_input.source_to_display(0) )
            ]
            
            fragments += inter[1:]
            separator_positions = [ fragment_list_len( fragments ) - 1 ]
            for i, fragment in enumerate(
                  islice( trans_fragments,
                          trans_input.source_to_display(
                             len( trans_input.document.text ) - 1
                          ) \
                          - trans_input.source_to_display(0)
                         ),
                  start = fragment_list_len( fragments )
            ):
               if fragment[1] == "\x1e":
                  fragments += inter
                  separator_positions += [ i ]
               else:
                  fragments += [ fragment ]
            separator_positions += [
               fragment_list_len( fragments )
            ]
            fragments += [ ("", "}") ]
            fragments += [ frag for frag in trans_fragments ]

            active_positions = [
               j + m * ( len( inter ) - 1 )
               for j,m in enumerate(
                  ( n
                    for i in range( len( separator_positions ) - 1 )
                    for n in (i,) * ( separator_positions[i+1]
                                      - separator_positions[i]
                                     )
                   ),
                  start = separator_positions[0] + 1 # wrong again!
               )
            ]
            active_positions += [ active_positions[-1] + 2 ]
            #breakpoint()
            def display_to_source( display_pos ):
               try:
                  return active_positions.index( display_pos )
               except ValueError:
                  return next( ( i for i,pos in enumerate( active_positions )
                                 if pos > display_pos
                                ),
                               len( fragments ) + 1
                              )

            def apt(p):
               try:
                  return active_positions[p]
               except IndexError:
                  q = trans_input,fragments
                  breakpoint()
               
            return Transformation(
               fragments,
               source_to_display = apt,#lambda p: active_positions[p],
               display_to_source = display_to_source
            )

      TextArea.__init__(
         self,
         text = "\x1e".join( ninjas ),
         multiline = False,
         prompt = FormattedText([ ("", "            }{ "),
                                 ]),
         input_processors = [
            ClotheNinjas(),
            AfterInput([ ("ansibrightblack", "  % assigned ninjas")
                        ])
         ]
      )

      kb = KeyBindings()

      @kb.add(
         'backspace',
         filter = has_focus( self ) \
           & Condition( lambda: self.document.cursor_position > 0 \
                          and self.text[ self.document.cursor_position - 1 ] \
                                == "\x1e" \
                          or self.document.cursor_position == len( self.text )
                       )
      )
      def dont_delete_( event ):
         event.app.output.bell()
      kb.add(
         'delete',
         filter = has_focus( self )\
           & Condition(
              lambda: self.document.cursor_position < len( self.text ) \
                and self.text[ self.document.cursor_position ] == "\x1e" \
                or self.document.cursor_position == len( self.text ) - 1
           )
      )(dont_delete_)

      self.control.key_bindings = merge_key_bindings((
         load_key_bindings(), nav_kb, kb
      ))

      self.buffer.read_only = Condition(
         lambda: self.document.cursor_position == len( self.text )
      )
      
class MoveLines():
   def __init__( self, move, pre_prompt = "" ):
      self.array = [
         TextAreaWithBindings(
            text = t,
            prompt = FormattedText([
               ("", pre_prompt if i == 0 else " " * len( pre_prompt ) ),
               (("ansicyan", "\\move") if i == 0 else ("", "    }")),
               ("", "{ ")
            ]),
            dont_extend_height=True,
            input_processors = [ AfterInput( FormattedText([
               ( "ansibrightblack", cmt )
            ]))]
         ) for i,(t,cmt) in enumerate( zip(
            ( move.time,  move.destination ),
            [ "  % time", "  % from / to" ]
         ))
      ] + [ NinjasLine( move.ninjanames ),
            Label( " " * len( pre_prompt ) + "}" )
           ]

   @property
   def __getitem__( self ):
      return self.array.__getitem__
   @property
   def __add__( self, other ):
      return self.array.__add__

class PropLines():
   def __init__( self, prop = NinjaProp( "", "", "", [] ) ):
      hard_focus = FocusableLabel( " ", dont_extend_width = True )
      hard_field = NarrowLabel( " " + prop.hardness )
      hard_kb = KeyBindings()
      @hard_kb.add('backspace')
      def none_(event):
         hard_field.text = " "
      def nt( n ):
         def set_hard( event ):
            hard_field.text = " " + str( n )
         return set_hard
      for n in range( 1, 6 ):
         hard_kb.add( str( n ) )( nt( n ) )

      self.array = [
         VSplit([ NarrowLabel( FormattedText([ ("ansicyan", "  \\prop"),
                                               ("", "{")
                                              ])),
                  hard_field,
                  hard_focus,
                  Label( FormattedText([
                     ("ansibrightblack", "  % difficulty on a scale of 1 - 5")
                  ]))
                 ], key_bindings = hard_kb
                )
         ] + [
            TextAreaWithBindings(
               text = data,
               prompt = "      }{ ",
               dont_extend_height=True,
               input_processors = [ AfterInput( FormattedText([
                  ( "ansibrightblack", cmt )
               ]) )]
            ) for data,cmt in zip(
               ( prop.name, prop.drawing ),
               ( "   % prop name",
                 "   % drawing (in TikZ format, see manual)"
                )
               )
         ] + [ ml for i,move in enumerate(prop.moves)
               for ml in MoveLines( move, "      }{" if i == 0 else "        " )
         ] + [ Label( "  }" ) ]

   @property
   def __getitem__( self ):
      return self.array.__getitem__

class NinjaLayout( Layout ):
   def __init__( self, material ):
      ps = [ PropLines( p ) for p in material.ninjaprops or [] ]
      point = Window( FormattedTextControl(
         FormattedText([("ansibrightblack italic", " [↲]: add prop")]),
         focusable = is_true( not bool( ps ) )
      ))

      Layout.__init__( self, ScrollablePane( HSplit([
         VSplit([ Label( FormattedText([ ("ansicyan", "\\ninjas"),
                                         ("", "{ ")
                                        ]),
                         dont_extend_width=True
                        ),
                  ConditionalContainer( point, has_focus( point ) )
                 ])
      ] + [
         l for p in ps for l in p
      ] + [
         Label( "}" )
      ], key_bindings = nav_kb )))
      self.focus( ( ps + [[ point ]] )[0][0] )


@kb.add('e')
def switch_( event ):
   event.app.layout = NinjaLayout( next( islice( r.materials, 0, None ) ) )

@kb.add('enter')
def add_prop( event ):
   f = Label( FormattedText([("[SetCursorPosition]", " ")]),
              dont_extend_width=True
             )
   dif_kb = KeyBindings()
   @dif_kb.add('backspace')
   def none_( event ):
      f.text = " "
   def nt( n ):
      def put( event ):
         f.text = FormattedText([ ("", str( n ) ),
                                  ("[SetCursorPosition]", " ")
                                 ])
         f.formatted_text_control.focusable = True
         event.app.layout.focus( t )
      return put
   for n in range( 1, 6 ):
      dif_kb.bindings.append( Binding( str( n ), nt( n ) ))
   f.formatted_text_control.key_bindings = dif_kb
   @dif_kb.add("down")
   def d_(event):
      event.app.layout.focus( l[1] )

   class VaugeSuggest( AutoSuggest ):
      def get_suggestion( self, _, doc ):
         return Suggestion( "   " + ", ".join(
            p.prop[ len(doc.text.strip()) : ] for p in testprops
            if p.prop.strip().lower().startswith( doc.text.strip().lower() )
         ) )

   t = TextArea( text = "", auto_suggest = VaugeSuggest() )
   l = [ VSplit([ NarrowLabel( "  \\prop{ " ),
                  f,
                  NarrowLabel( FormattedText([
                     ("ansibrightblack", "  % difficulty on a scale of 1 - 5")
                  ]))
                 ]),
         VSplit([ NarrowLabel( "  }{ "),
                  FloatContainer(
                     t,
                     [ Float( Label( FormattedText([( "ansibrightblack",
                                                      "  % prop name"
                                                     )])),
                              left = 0,
                              hide_when_covering_content = True
                             )]
                  )
                  # ,
                  # NarrowLabel( FormattedText([("ansibrightblack",
                  #                              "   % prop name"
                  #                              )]))
                 ], key_bindings=load_key_bindings() ),
         Label( "  }" )
        ]
   c = event.app.layout.container.children
   event.app.layout.container = HSplit( c[:-1] + l + c[-1:] )
   # pprint( event.app.layout.container.children )
   event.app.layout.focus( f )

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

