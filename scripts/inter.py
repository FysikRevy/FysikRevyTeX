import os,sys,re

from pprint import pprint
from itertools import chain, dropwhile, islice
from copy import copy
from dataclasses import dataclass
from locale import strxfrm
from collections import defaultdict

from more_itertools import stagger, intersperse
from ordered_set import OrderedSet

from prompt_toolkit import Application, ANSI, PromptSession
from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.application import get_app
from prompt_toolkit.formatted_text import to_formatted_text, FormattedText, fragment_list_len
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, HorizontalAlign, VerticalAlign, ConditionalContainer, ScrollOffsets, FloatContainer, Float, DynamicContainer
from prompt_toolkit.layout.scrollable_pane import ScrollablePane
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.processors import AfterInput, Processor, explode_text_fragments, Transformation, ConditionalProcessor
from prompt_toolkit.layout.menus import CompletionsMenuControl
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import Binding
from prompt_toolkit.key_binding.bindings.named_commands import end_of_line
from prompt_toolkit.widgets import Label, Button, TextArea
from prompt_toolkit.filters import has_focus, Never, Always, is_true, Condition, to_filter
from prompt_toolkit.styles import Style, DynamicStyle, merge_styles
from prompt_toolkit.output import Output
from prompt_toolkit.document import Document
from prompt_toolkit.utils import Event
from prompt_toolkit.completion import WordCompleter, ConditionalCompleter

sys.path.append( os.getcwd() )
os.chdir( "E:/thebe/Git/revymanus2025/" )

from classy_revy import Revue, Scene
from base_classes import NinjaProp, NinjaMove
from tex import TeX
from clobberers import replace_ninjas

_NAME_FIELD_RE = re.compile( "([^\x1e]*(?:[^\x1e\\s]|[^\x1e\\S](?!$))?)" )

class NarrowLabel( Label ):
   def __init__( self, *args, **kwargs ):
      if len(args) < 4 and "dont_extend_width" not in kwargs:
         kwargs["dont_extend_width"] = True
      try:
         super().__init__( *args, **kwargs )
      except TypeError as e:
         try:
            style_arg = args[1]
            args[1] = ""
         except IndexError:
            try:
               style_arg = kwargs["style"]
               del kwargs["style"]
            except KeyError:
               raise e
         super().__init__( *args, **kwargs )
         fixed_style = self.window.style
         self.window.style = lambda: fixed_style + " " + style_arg()

class FocusableLabel( NarrowLabel ):
   def __init__( self, text = "", *args, **kwargs ):
      super().__init__( text, *args, **kwargs )
      self.formatted_text_control.focusable = Always()

class HotSpot( VSplit ):
   def __init__( self, help_text = None, key_bindings = KeyBindings(),
               *args_for_label, **kwargs_for_label
              ):
      try:
         text = args_for_label[0]
      except IndexError:
         try:
            text = kwargs_for_label["text"]
         except KeyError:
            text = ""

      self.spot = FocusableLabel( " " )
      self.spot.formatted_text_control.key_bindings = key_bindings
      l = NarrowLabel(
         to_formatted_text( text ) + formatted_control( help_text ),
         *args_for_label[1:],
         **{ k: kwargs_for_label[k] for k in kwargs_for_label if k != "text" }
      )
      super().__init__([ self.spot,
                         ConditionalContainer( l, has_focus( self.spot )) ])

class ColdSpot( HotSpot ):
   def __init__( self, *args, **kwargs ):
      super().__init__( *args, **kwargs )
      self.spot.formatted_text_control.focusable = has_focus( self.spot )

def formatted_control( text ):
   if not text:
      return FormattedText((("", ""),))
   return FormattedText(
      (("italic", " [{}]".format(text) ),)
   )

r = Revue.fromfile("aktoversigt.plan")
items = [ m.title for m in r.materials ]

# items = ["one","two","three"]
# controls = [ control("w/r/n") for _ in items ]
number_style = Style.from_dict({"number": "ansibrightblack" })
def highlightable_number( ndex, of_number ):
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
      if isinstance( mat, Scene ) and g[1] == mat\
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
@nav_kb.add('enter')
def accept( event ):
   buffer = event.app.layout.current_buffer
   if buffer.complete_state \
         and buffer.complete_state.complete_index != None:

      buffer.apply_completion(
         buffer.complete_state.completions[
            buffer.complete_state.complete_index
         ]
      )

   end_of_line( event )

class TextAreaWithBindings( TextArea ):
   def __init__( self, *args, **kwargs ):
      TextArea.__init__( self, *args, **kwargs )
      self.control.key_bindings = merge_key_bindings((
         load_key_bindings(), nav_kb
      ))

class NinjasLine(TextArea):
   def __init__( self, layout, ninjas, style = lambda: "" ):
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
            
            separator_positions = [ ( 0,0 ),
                                    ( fragment_list_len( fragments ) - 1,
                                      fragment_list_len( inter[1:] )
                                     )
                                   ]
            fragments += inter[1:]
            for i, fragment in enumerate(
                  islice( trans_fragments,
                          trans_input.source_to_display(
                             len( trans_input.document.text )
                          ) \
                          - trans_input.source_to_display(0)
                         ),
                  start = trans_input.source_to_display(0) + 1
            ):
               if fragment[1] == "\x1e":
                  fragments += inter
                  separator_positions += [( i,
                                            fragment_list_len( inter ) \
                                            + separator_positions[-1][1] \
                                            - 1
                                           )
                                          ]
               else:
                  fragments += [ fragment ]
            separator_positions += [
               ( trans_input.source_to_display(
                  len( trans_input.document.text )
                 ),
                 separator_positions[-1][1] + 1
                )]
            fragments += [ ("", "}") ]
            fragments += [ frag for frag in trans_fragments ]

            active_positions = [
               j + m
               for j,m in enumerate(
                  ( n
                    for i in range( len( separator_positions ) - 1 )
                    for n in ( separator_positions[i][1], ) \
                             * ( separator_positions[i+1][0]
                                 - separator_positions[i][0]
                                )
                   )
               )
            ]
            # breakpoint()
            def display_to_source( display_pos ):
               try:
                  return active_positions.index( display_pos )
               except ValueError:
                  return next( ( i for i,pos in enumerate( active_positions )
                                 if pos > display_pos
                                ),
                               len( fragments ) + 1
                              )

            def source_to_display( position ):
               try:
                  return active_positions[ position ]
               except IndexError:
                  # q = trans_input,fragments
                  # breakpoint()
                  return position + separator_positions[-1][1]
               
            return Transformation(
               fragments,
               source_to_display = source_to_display,
               display_to_source = display_to_source
            )

      class TabHelp( Processor ):
         def apply_transformation( self, trans_input ):
            if not trans_input.document.text:
               return Transformation( trans_input.fragments )

            # breakpoint()

            tab_help = FormattedText([("italic", " [tab]")])
            shift = fragment_list_len( tab_help )

            help_spot = trans_input.document.text.find(
               "\x1e", trans_input.document.cursor_position
            )
            if help_spot < 0:
               help_spot = len( trans_input.document.text ) - 1
            help_spot = trans_input.source_to_display( help_spot )

            fragments = explode_text_fragments( trans_input.fragments )
            return Transformation(
               fragments[:help_spot] + tab_help + fragments[help_spot:],
               source_to_display = lambda p: p + (
                  shift if p > help_spot else 0
               ),
               display_to_source = \
                 lambda p: p if p <= help_spot \
                             else help_spot if p <= help_spot + shift \
                             else p + shift
            )

      TextArea.__init__(
         self,
         text = "\x1e".join( ninjas ),
         focus_on_click = True,
         prompt = FormattedText([ ("", "            }{ "),
                                 ]),
         dont_extend_height = True
      )
      fixed_style = self.window.style
      self.window.style = lambda: fixed_style + " " + style()
      cursor_at_field_end = Condition(
         lambda: self.document.cursor_position + 1 == len( self.document.text )\
                   or self.document.cursor_position < len( self.document.text )\
                   and self.document.text[ self.document.cursor_position ]\
                          == "\x1e"
      )
      self.control.input_processors += [
            ConditionalProcessor(
               TabHelp(),
               has_focus( self.buffer ) \
                 & cursor_at_field_end \
                 & Condition(
                    lambda: not self.buffer.complete_state
                 )
            ),
            ClotheNinjas(),
            ConditionalProcessor( AfterInput([ ("italic", " [+]" ) ]),
                                  has_focus( self.buffer )
                                 ),
            AfterInput([ ("ansibrightblack", "  % assigned ninjas")
                        ])
         ]

      class CompleteSelectionHelp():
         def get( _, key, fallback = "" ): # don't shadow outer self
            index = self.buffer.complete_state.complete_index
            count = len( self.buffer.complete_state.completions )
            try:
               prev_index, next_index = ( (index + s) for s in (-1,1) )
            except TypeError:
               prev_index, next_index = -1, 0

            breakpoint()
            return FormattedText((("italic", "[tab]"),)) \
               if count == next_index \
               else FormattedText((("italic", "[s-tab]"),)) \
               if count == prev_index \
               else fallback
      self.completer = ConditionalCompleter(
         WordCompleter(
            lambda: layout.updated_ninjanames() - { n for n in self },
            ignore_case = True,
            pattern = _NAME_FIELD_RE# ,
            # meta_dict = CompleteSelectionHelp()
         ),
         cursor_at_field_end
      )
      
      def on_move( event = None, ignore_focus = False ):
         if self.buffer.selection_state \
               and "\x1e" in self.document.text[
                  slice( *sorted((
                     self.buffer.selection_state.original_cursor_position,
                     self.document.cursor_position
                  )))
               ]:
            self.buffer.selection_state = None
            
         cursor_field_index = sum(
            1 for c in self.document.text[ : self.document.cursor_position ]
            if c == "\x1e"
         )
         fields = self.document.text.split( "\x1e" )
         pre_fields = fields[ : cursor_field_index ]
         post_fields = fields[ cursor_field_index + 1 : ]
         pre_dirty_length = len( "\x1e".join( pre_fields ) )
         were_post_fields = len( post_fields )
         if ignore_focus \
               or self.document.cursor_position == len( self.document.text ) \
               or not is_true( has_focus( self ) ):
            pre_dirty_length += len(
               re.match( " *", fields[ cursor_field_index ] )[0]
            )
            were_post_fields = self.document.cursor_position \
                                  == len( self.document.text )
            post_fields = [ fields[ cursor_field_index ] ] + post_fields
            cursor_field = []
         else:
            cursor_field = [ fields[ cursor_field_index ] ]
         pre_fields, post_fields = (
            [ ff for ff in ( f.strip() for f in x_fields )
              if ff
             ] for x_fields in ( pre_fields, post_fields )
         )
         pre_shift = len( "\x1e".join( pre_fields ) ) - pre_dirty_length
         pre_fields += cursor_field
         try:
            post_fields[-1] += " "
         except IndexError:
            if were_post_fields:
               try:
                  pre_fields[-1] += " "
               except IndexError:
                  pass

         fields = pre_fields + post_fields

         self.document = Document(
            "\x1e".join( fields ),
            self.document.cursor_position + pre_shift
         )
      self.buffer.on_cursor_position_changed = Event( self.buffer, on_move )

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
      @kb.add(
         'delete',
         filter = has_focus( self )\
           & Condition(
              lambda: self.document.cursor_position < len( self.text ) \
                and self.text[ self.document.cursor_position ] == "\x1e" \
                or self.document.cursor_position == len( self.text ) - 1
           )
      )
      def dont_delete_( event ):
         event.app.output.bell()

      @kb.add('+')
      @kb.add('\\', filter = Condition(
         lambda: self.document.cursor_position == len( self.document.text )
      ))
      def plus_( event ):
         self.document = \
            Document( self.document.text[:-1] \
                        + ("\x1e " if self.document.text else " "),
                      len( self.document.text )
                     )
      @kb.add('up')
      def up_( event ):
         on_move( ignore_focus = True )
         event.app.layout.focus_previous()
      @kb.add('down')
      def down_( event ):
         on_move( ignore_focus = True )
         event.app.layout.focus_next()

      self.control.key_bindings = merge_key_bindings((
         load_key_bindings(), nav_kb, kb
      ))

      self.buffer.read_only = Condition(
         lambda: self.document.cursor_position == len( self.text )
      )

   def __getitem__( self, i ):
      return self.document.text[:-1].split("\x1e")[i]
   def __setitem__( self, i, item ):
      self.document.text = "\x1e".join(
         item if ii == i else n
         for i,n in enumerate( self.document.text[:-1].split("\x1e" ) )
      ) + " "

   def __iter__( self ):
      return self.document.text[:-1].split("\x1e").__iter__()

   def __len__( self ):
      return sum( 1 for c in self.document.text if c == "\x1e" ) + 1
      
class MoveLines(NinjaMove):
   def __init__( self, layout, prop, move,
                 pre_prompt = "",
                 style = lambda: ""
                ):
      self.pre_prompt = pre_prompt
      self.scene = move.scene
      self.layout = layout
      def attach_processors( text_area, cmt ):
         cursor_at_end = Condition(
            lambda: text_area.document.cursor_position \
                       == len( text_area.document.text )
         )
         
         text_area.control.input_processors += [
            AfterInput( " " ),
            ConditionalProcessor(
               AfterInput( FormattedText((("italic", "[tab] "),)) ),
               has_focus( text_area ) & cursor_at_end & Condition(
                  lambda: not text_area.buffer.complete_state
               )
            ),
            AfterInput( FormattedText([
               ( "ansibrightblack", cmt )
            ]))]
         fixed_style = text_area.window.style
         text_area.window.style = lambda: fixed_style + " " + self._delete_selection()
         if text_area.completer:
            text_area.completer = ConditionalCompleter(
               text_area.completer, cursor_at_end
            )
         return text_area

      del_kb = KeyBindings()
      @del_kb.add("-")
      @del_kb.add("backspace")
      @del_kb.add("delete")
      def confirm_minus_move( event ):
         index = prop.move_lines.index( self )
         del prop.move_lines[ index ]
         try:
            goto = prop.move_lines[ index ][0]
         except IndexError:
            try:
               goto = prop.move_lines[ -1 ][0]
            except IndexError:
               goto = prop.default_move[0]

         event.app.layout.focus( goto )

      confirm_delete = ColdSpot( "press again to confirm", del_kb )
      def delete_selection():
         return " ".join(
            t for t in [
               "class:selected" if layout.has_focus( confirm_delete ) else "",
               style()
            ] if t
         )
      self._delete_selection = delete_selection

      meta_kb = KeyBindings()
      @meta_kb.add('+')
      def plus_move( event ):
         index = prop.move_lines.index( self ) + 1
         new_move = MoveLines( layout, prop,
                               NinjaMove( "", "", [] ),
                               " " * len( pre_prompt )
                              )
         prop.move_lines = prop.move_lines[:index] \
            + [ new_move ]\
            + prop.move_lines[index:]
         event.app.layout.focus( new_move[0] )
      @meta_kb.add("-")
      def minus_move( event ):
         event.app.layout.focus( confirm_delete.spot )

      self.ninjanames = move.ninjanames # sets ninjas_line,
                                        # requires self._delete_selection
      self.array = [
         attach_processors(
            TextAreaWithBindings(
               text = t,
               prompt = FormattedText([
                  ("", self.pre_prompt if i == 0
                          else " " * len( self.pre_prompt )
                   ),
                  (("ansicyan", "\\move") if i == 0 else ("", "    }")),
                  ("", "{ ")
               ]),
               dont_extend_height=True,
               completer = WordCompleter( cpl,
                                          ignore_case = True,
                                          sentence = True
                                         )
            ),
            cmt
         ) for i,(t,cmt,cpl) in enumerate( zip(
            ( move.time,              move.destination ),
            ( " % time",              " % from / to" ),
            ( layout.updated_times, layout.updated_destinations )
         ))
      ] + [ self.ninjas_line,
            VSplit([
               NarrowLabel( " " * len( pre_prompt ) + "} ",
                            style = self._delete_selection
                           ),
               HotSpot( "+/-", meta_kb ),
               confirm_delete,
               NarrowLabel(
                  FormattedText((( "ansibrightblack", " % add more moves"),)),
                  style = style,
                  dont_extend_width = False
               )
            ])
           ]

   @property
   def time( self ):
      return self.array[0].document.text
   @time.setter
   def time( self, time ):
      self.array[0].document.text = time
   @property
   def destination( self ):
      return self.array[1].document.text
   @destination.setter
   def destination( self, destination ):
      self.array[1].document.text = destination
   @property
   def ninjanames( self ):
      return ninjas_line
   @ninjanames.setter
   def ninjanames( self, ninjanames ):
      self.ninjas_line = NinjasLine(
         self.layout, ninjanames, self._delete_selection
      )

   @property
   def __getitem__( self ):
      return self.array.__getitem__
   @property
   def __add__( self, other ):
      return self.array.__add__

class PropLines( NinjaProp ):
   move_prompt = "      }{"
   def move_lines_from_ninjamoves( self, ninjamoves ):
      return [
         self.movelines_from_ninjamove(
            move, self.move_prompt if i == 0 else " " * len(self.move_prompt)
         ) for i,move in enumerate( ninjamoves )
      ]
   def __init__( self, layout, prop = NinjaProp( "", "", "", [] )
                ):
      del_kb = KeyBindings()
      @del_kb.add('-')
      @del_kb.add('backspace')
      @del_kb.add('delete')
      def vanish( event ):
         index = layout.ps.index( self )
         del layout.ps[ index ]
         try:
            land = layout.ps[ index ][0]
         except IndexError:
            try:
               land = layout.ps[-1][0]
            except IndexError:
               land = layout.container\
                            .content\
                            .content\
                            .get_container()\
                            .children[0]
         event.app.layout.focus( land )
      delete_spot = ColdSpot( "press again to confirm", del_kb )
      def delete_selected():
         return "class:selected" if layout.has_focus( delete_spot.spot ) else ""

      self.movelines_from_ninjamove = lambda \
         ninjamove, move_prompt = " " * len( self.move_prompt ): \
            MoveLines( layout, self, ninjamove, move_prompt,
                       style = delete_selected
                      ) \
            if not isinstance( ninjamove, MoveLines ) else ninjamove
      self.move_lines = self.move_lines_from_ninjamoves( prop.moves )
      self.hard_field = NarrowLabel( " " + prop.hardness )
      hard_focus = FocusableLabel( " " )
      hard_kb = KeyBindings()
      @hard_kb.add('backspace')
      def none_(event):
         self.hard_field.text = " "
      def nt( n ):
         def set_hard( event ):
            self.hard_field.text = " " + str( n )
         return set_hard
      for n in range( 1, 6 ):
         hard_kb.add( str( n ) )( nt( n ) )

      class PropArea( TextAreaWithBindings ):
         def __init__( self,
                       focused_help: Processor | None = None,
                       *args, **kwargs
                      ):
            def_args = ({'pos': 16, 'kw': 'dont_extend_height',
                         'val': True
                         },
                        {'pos': 24, 'kw': 'prompt',
                         'val': "      }{ ",
                         }
                        )
            while True:
               try:
                  super().__init__(
                     *args,
                     **( { d['kw']: d['val'] for d in def_args
                           if d['pos'] >= len( args )
                          } \
                         | { k: kwargs[k] for k in kwargs
                             if k not in [ "input_processors", "completer" ]
                            }
                        )
                  )
               except TypeError as e:
                  try:
                     style_arg = args[1]
                     args[1] = ""
                  except IndexError:
                     try:
                        style_arg = kwargs["style"]
                        del kwargs["style"]
                     except KeyError:
                        raise e
               else:
                  try:
                     fixed_style = self.window.style
                     self.window.style = lambda: fixed_style + " " + style_arg()
                  except NameError:
                     pass
                  break

            cursor_at_end = Condition(
               lambda: self.document.cursor_position == \
                         len( self.document.text )
            )            
            def cond_comp( completer ):
               return ConditionalCompleter( completer, cursor_at_end )
            try:
               self.completer = cond_comp( args[5] )
            except IndexError:
               try:
                  self.completer = cond_comp( kwargs['completer'] )
               except KeyError:
                  pass

            try:
               input_processors = args[25] or []
            except IndexError:
               try:
                  input_processors = kwargs['input_processors'] or []
               except KeyError:
                  if not focused_help:
                     return
                  input_processors = []

            help_processor = [
               ConditionalProcessor(
                  focused_help, has_focus( self.buffer ) & cursor_at_end
               )
            ] if focused_help else []

            self.control.input_processors += \
               [ AfterInput( " " ) ] + help_processor + input_processors

      meta_kb = KeyBindings()
      @meta_kb.add('+')
      def plus_prop( event ):
         index = layout.ps.index( self ) + 1
         new_prop_lines = PropLines(
            layout,
            NinjaProp( "", "", "", [ # NinjaMove( "", "", [] )
                                    ] )
         )
         layout.ps = layout.ps[:index] + [ new_prop_lines ] + layout.ps[index:]
         event.app.layout.focus( new_prop_lines[0] )
      @meta_kb.add('-')
      def minus_prop( event ):
         event.app.layout.focus( delete_spot.spot )

      self.pre_array = [
         VSplit([ NarrowLabel( FormattedText([ ("ansicyan", "  \\prop"),
                                               ("", "{")
                                              ])),
                  self.hard_field,
                  hard_focus,
                  Label( FormattedText([
                     ("ansibrightblack", "  % difficulty on a scale of 1 - 5")
                  ]))
                 ],
                key_bindings = hard_kb,
                style = delete_selected
                ),
            PropArea(
               ConditionalProcessor(
                  AfterInput( FormattedText((("italic", "[tab] "),))),
                  Condition( lambda: not layout.current_buffer.complete_state )
               ),
               text = prop.name,
               style = delete_selected,
               input_processors = [ AfterInput( FormattedText([
                  ( "ansibrightblack", " % prop nane" )
               ]) )],
               completer = WordCompleter( layout.updated_propnames,
                                          ignore_case = True
                                         )
            ),
            PropArea(
               text = prop.drawing,
               style = delete_selected,
               input_processors = [ AfterInput(
                  FormattedText((
                     ("ansibrightblack",
                      " % drawing (in TikZ format, see manual. Not required)"
                      ),
                     ))
                  )]
            )
      ]

      move_meta_kb = KeyBindings()
      @move_meta_kb.add('+')
      def default_plus_move( event ):
         self.move_lines = [ MoveLines(
            layout, self, NinjaMove( "", "", [] ), self.move_prompt,
            style = delete_selected
         ) ]
         event.app.layout.focus( self.move_lines[0][0] )
      self.default_move = [ VSplit([
         NarrowLabel( FormattedText((("", self.move_prompt),)) ),
         HotSpot( "+", move_meta_kb ),
         NarrowLabel( FormattedText((("ansibrightblack", "  % add move"),)))
      ]) ]

      self.post_array = [ VSplit([
         NarrowLabel( "  } ", style = delete_selected ),
         HotSpot( '+/-', meta_kb ),
         delete_spot,
         NarrowLabel(
            FormattedText((("ansibrightblack", "  % add more props"),))
         )
      ]) ]
   
   @property
   def array( self ):
      return self.pre_array \
         + ( [ l for ml in self.move_lines for l in ml ] or self.default_move )\
         + self.post_array
   @property
   def hardness( self ):
      return self.hard_field
   @hardness.setter
   def hardness( self, hardness ):
      self.hard_field = hardness
   @property
   def name( self ):
      return self.pre_array[1].document.text
   @name.setter
   def name( self, name ):
      self.pre_array[1].document.text = name
   @property
   def drawing( self ):
      return self.pre_array[2].document.text
   @drawing.setter
   def drawing( self, drawing ):
      self.pre_array[2].document.text = drawing
   @property
   def moves( self ):
      class LineMaker():
         def __setitem__( self, i, item ):
            self.move_lines[ i ] = self.movelines_from_ninjamove( item )
         def __getattr__( self, attr ):
            return getattr( self.move_lines, attr )
               
      return LineMaker()
   @moves.setter
   def moves( self, moves ):
      self.move_lines = self.move_lines_from_ninja_moves( moves )

   @property
   def __getitem__( self ):
      return self.array.__getitem__

# hack in completion navigation help
CompletionsMenuControl._show_meta = lambda self, completion_state: True
CompletionsMenuControl.__get_menu_meta_width = \
   CompletionsMenuControl._get_menu_meta_width
completion_back_help, completion_fwd_help = \
   FormattedText((("italic", "[s-tab]"),)), \
   FormattedText((("italic", "[tab]"),))
help_width = max( fragment_list_len( help )
                  for help in (completion_back_help, completion_fwd_help)
                 )
CompletionsMenuControl._get_menu_meta_width = \
   lambda self, max_width, completion_state: \
    max( self.__get_menu_meta_width( max_width, completion_state ),
         help_width
        )
def hacked_get_menu_item_meta_fragments(
      self, completion, is_current_completion, width
):
   complete_state = get_app().current_buffer.complete_state
   index = -1 if complete_state.complete_index == None \
      else complete_state.complete_index
   help = FormattedText((("",""),))
   try:
      completion_index = complete_state.completions.index( completion )
      if completion_index == index - 1:
         help = completion_back_help
      elif completion_index == index + 1:
         help = completion_fwd_help
   except ValueError:
      pass
      
   return to_formatted_text(
      help + [(""," " * (width - fragment_list_len( help )))],
      style = "class:completion-menu.meta.completion.current"\
              if is_current_completion \
              else "class:completion-menu.meta.completion"
   )
CompletionsMenuControl._get_menu_item_meta_fragments \
   = hacked_get_menu_item_meta_fragments

class NinjaLayout( Layout ):
   # TODO: pull the defaults out of the .tex template?
   times = OrderedSet(( "\\before", "\\during", "\\after" ))
   destinations = OrderedSet(( "\\bagT", "\\sideT" ))
   
   def __init__( self, material ):
      self.material = material
      self.ps = []
      self.ninjanames = OrderedSet( n.name for n in r.ninjas
         if material in ( nm.scene for nm in n.ninjamoves )
      ) \
      | OrderedSet(
         a.name for a in r.actors if material in (
            rl.material for rl in a.roles + a.instructorships
         )
      ) \
      | OrderedSet( n.name for n in r.ninjas ) \
      | OrderedSet( a.name for a in r.actors )
      self.propnames = OrderedSet(
         sorted( ( p.prop for p in material.props or [] ),
                 key = strxfrm
                )
      )
      self.ps = [ PropLines( self, p )
                  for p in material.ninjaprops or []
                 ]

      meta_kb = KeyBindings()
      @meta_kb.add('+')
      def initial_plus( event ):
         self.ps = [ PropLines(
            self, NinjaProp( "", "", "", [ NinjaMove( "", "", [] ) ] )
         )] + self.ps
         self.focus( self.ps[0][0] )

      point = HotSpot( '+', meta_kb )

      self.content_hsplit = DynamicContainer(
         lambda: HSplit([
            VSplit([ Label( FormattedText([ ("ansicyan", "\\ninjas"),
                                            ("", "{ ")
                                           ]),
                            dont_extend_width=True
                           ),
                     point
                    ])
         ] + [
            l for p in self.ps for l in p
         ] + [
            Label( "}" )
         ], key_bindings = nav_kb )
      )

      Layout.__init__( self, FloatContainer(
         ScrollablePane( self.content_hsplit ),
         floats = [
            Float( content = Window(CompletionsMenuControl()),
                   xcursor = True,
                   ycursor = True
                  )
         ]
      ))
      self.focus( ( self.ps + [[ point ]] )[0][0] )

   def updated_ninjanames( self ):
      return OrderedSet( sorted( ( n for p in self.ps
                                   for m in p.move_lines
                                   for n in m.ninjas_line
                                   if n
                                  ),
                                 key = strxfrm
                                ) ) \
             | self.ninjanames
   def updated_times( self ):
      return self.times | OrderedSet(
         sorted( ( m.time for p in self.ps
                   for m in p.move_lines
                   if m.time
                  ),
                 key = strxfrm
                )
      )
   def updated_destinations( self ):
      return self.destinations | OrderedSet(
         sorted( ( m.destination for p in self.ps
                   for m in p.move_lines
                   if m.destination
                  ),
                 key = strxfrm
                )
      )
   def updated_propnames( self ):
      return self.propnames - { p.name for p in self.ps }

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

