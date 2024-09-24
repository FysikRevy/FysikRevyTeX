# coding: utf-8
import shutil
from multiprocessing.managers import SyncManager
from itertools import cycle,count,islice
from math import ceil,floor
from time import time

headers = (  "Proces #{}"
            ,"Proc#{}"
            ,"Pr{}"
            ,"P{}"
            ,"{}"
           )
indices = "abcdefghijklmnopqrstuvwxyzæøå" \
          "ABCDEFGHIJKLMNOPQRSTUVWXYZÆØÅ" \
          "0123456789" \
          "бгджзилпфцчшьюя" \
          "БГДЖЗИЛПФЦЧШЬЮЯ" \
          "αβγδεζηθικλμνξοπρσςτυφχψω" \
          "ΔΘΛΞΣΦΨΩ"
indicators = ".-=≡#"
file_list_column_width = 24
fmts = {  "none": "\033[0m"
         ,"info": "\033[34m"
         ,"success": "\033[42m"
         ,"warn": "\033[43m"
         ,"error": "\033[41m"
         ,"skip": "\033[37;100m"
        }

def text_effect( text, fmt ):
   return fmts[ fmt ] + text + fmts["none"]
def task_start( letter ):
   return text_effect( letter, "info" )

yes, maybe, no, skip = ( text_effect( ch, st ) \
                         for st,ch in zip(
                               ["success","warn","error","skip"]
                             , ["✓",      "?",   "!",    "→"   ]
                         )
                        )

class Output:
   "implement PoolObject's interface for the old style output."
    def begin( self, pid, taskname ):
        self.taskname = "{:<42}".format(
            "\033[0;37;1m{}:\033[0m".format(taskname)
        )
    def activity( self, pid, number ):
        pass
    def skipped( self, pid ):
        pass
    def success( self, pid ):
        print( self.taskname + "\033[0;32m Success!\033[0m" )
    def done_with_warnings( self, pid ):
        print( self.taskname + "\033[0;33m Had Errors!\033[0m" )
    def failed( self, pid ):
        print( self.taskname + "\033[0;31m Failed!\033[0m" )

class PoolOutput:
   sized_caches_defaults = (( "_acts", 0 )
                           ,( "_status", None )
                           ,( "_newtask", None )
                           )
   def __init__( self, n_processes, min_refresh_interval = 1 ):
      self._clonk_count = 0
      self._queue = tuple()
      self._commands = []
      self.n_processes = n_processes
      self._resize_caches( 0 )
      self._proc_map = dict()
      self._max_act_queue = [0] * 4
      self._bpm = min_refresh_interval
      self._follow_commands = self._command_follower

   @property
   def n_processes( self ):
      return self._n

   @n_processes.setter
   def n_processes( self, x ):
      self._n = x
      self.cell_width = max( 1,
                             floor( shutil.get_terminal_size().columns / x )
                            )
      try:
         old_strs = self.strs
      except AttributeError:
         old_strs = []
      self.strs = [ s[ 1 - self.cell_width : ] for s in old_strs[:x] ]\
                   + [ "." * min( self._clonk_count, self.cell_width - 1 ) ]\
                     * ( x - len ( old_strs ) )

   def _resize_caches( self, new_size ):
      # sized caches with defaults:
      for s in self.sized_caches_defaults:
         try:
            old = getattr( self, s[0] )
         except AttributeError:
            old = []
         setattr( self, s[0],
                  old[:new_size] + [ s[1] ] * ( new_size - len( old ) )
                 )

   def _empty_caches( self ):
      newtask_def = next( d for d in self.sized_caches_defaults
                          if d[0] == "_newtask"
                         )
      try:
         self._newtask = [ nt if st else newtask_def[1]
                           for nt,st in zip( self._newtask, self._status )
                          ]
      except AttributeError:
         pass
      
      for s in self.sized_caches_defaults:
         if s[0] == "_newtask":
            continue
         try:
            l = len( getattr( self, s[0] ) )
         except AttributeError:
            pass
         else:
            setattr( self, s[0], [ s[1] ] * l )

   def _map( self, pid ):
      try:
         tn = self._proc_map[ pid ]
      except KeyError:
         tn = len( self._proc_map )
         self._proc_map[ pid ] = tn
         self._resize_caches( tn + 1 )

      return tn

   def _map_drop( self, index ):
      self._proc_map = { pid: (i if i < index else i - 1) \
                        for pid, i in items( self._proc_map ) \
                        if i != index
                       }
      for s in self.sized_caches_default:
         old = getattr( self, s[0] )
         setattr( self, s[0], old[ : index ] + old[ index+1 : ] )

   def _map_move( self, fr, to ):
      for s in self.sized_caches_default:
         old = getattr( self, s[0] )
         old[ to ] = old[ fr ]
         setattr( self, s[0], old )
      for pid in self._proc_map:
         if self._proc_map[ pid ] == to:
            self._map_drop( fr ) # probably breaks the iterator
            self._proc_map[ pid ] = fr
            break
      else:                     # nobreak
         # oh, dear ... maybe:
         raise IndexError(
            "proc_map has no entry pointing to index {}".format( to )
         )

   def _queue_update_info( self, prns ):
      print( "\n  Tilføjet til kø:" )
      print_columnized( *prns )

   def _legend( self ):
      print( "  Multiprocesmonitor:" )
      print( "Nuværende opgave: {}".format( task_start( indices[0] ) ), end="" )
      print( ", aktivitet: " + indicators, end="" )
      print( ", resultat: {}{}{}{}".format( yes, maybe, no, skip ) )

   def _proc_headers( self ):
      try:
         header_format = next(
            header for header in headers
            if len( header.format( self.n_processes ) ) < self.cell_width
         )
         cell_format = "{:^" + str( self.cell_width - 1 ) + "}|"
         for p in range( self.n_processes ):
            print( cell_format.format( header_format.format( p + 1 ) ), end="" )
         print()
      except StopIteration:
         cell_format = "{:^{}}|"[ : self.cell_width + 5 ]
         height = len( "{}".format( self.n_processes ) )
         ns = [ "{:>{}}".format( n + 1, height )
                for n in range( self.n_processes )
               ]
         print( "\n".join(
            [ "".join([ cell_format.format( n[d], max( 1, self.cell_width - 1 ))
                        for n in ns ])
              for d in range( height )
             ]
         ))

   def _preamble_once( self ):
      self._preamble_once = lambda *_: None # never to be seen again
      print()
      self._legend()
      self._proc_headers()
      self._clonk_time = time()

   def _enqueue_command( self, *args, command = None ):
      command = command or self._set_status
      self._preamble_once()
      self._commands += [( command, *args )]
      self._follow_commands()

   def _set_status( self, pid, status ):
      tn = self._map( pid )
      while self._status[ tn ] or self._newtask[ tn ]:
         self._clonk()
      self._status[ tn ] = status

   def _set_newtask( self, pid, taskname ):
      tn = self._map( pid )
      while self._newtask[ tn ]:
         self._clonk()
      try:
         self._newtask[ tn ] = task_start(
            next( c for c,n in zip( cycle( indices ), self._queue ) \
                  if n == taskname
                 )
         )
      except StopIteration:
         raise KeyError( "Unqueued taskname: '{}'".format( taskname ) )

   def _clonk( self ):
      # next line?
      if self._clonk_count >= max( 1, self.cell_width - 1 ):
         print()
         self.strs = [ "" ] * len( self.strs )
         self._clonk_count = 0

      # decide which character to print
      self._max_act_queue = self._max_act_queue[1:] \
         + [ max( self._acts or [0] ) ]
      max_act = max( self._max_act_queue ) or 1 # classic
      for i,s in enumerate( self.strs ):
         try:
            t = self._status[i] or self._newtask[i]
         except IndexError:
            t = None
         if t:
            self.strs[i] += t
            continue
         try:
            a = self._acts[i]
         except IndexError:
            a = 0
         self.strs[i] += indicators[
            ceil( a / max_act * (len( indicators ) - 1 ))
         ]
      self._clonk_count += 1
      self._clonk_time = time()
      self._empty_caches()
      
      # try to keep up with pid change
      while len( self._proc_map ) > self.n_processes:
         try:
            inactive = next(
               i for i, a, t in zip( count(), self._acts, self._status )
               if not a and not t
            )
         except StopIteration:
            break
         else:
            self._map_move( self.n_processes, inactive )

      # pull the lever, _clonk
      print( "\r", end="" )
      for s in self.strs[ : self.n_processes ]:
         print( s + " " * ( self.cell_width - self._clonk_count ), end="" )
         
   def _refresh_running( self ):
      try:
         if time() - self._clonk_time >= self._bpm:
            self._clonk()
      except AttributeError:
         pass

   def _command_follower( self ):
      # something, something, "reentrancy"...
      self._follow_commands = lambda *_: None
      while self._commands:
         c, self._commands = self._commands[0], self._commands[1:]
         c[0]( *c[1:] )
      self._follow_commands = self._command_follower

   def end_output( self ):
      "should only be called when no further signals are coming."
      
      while any( self._status + self._newtask + self._acts ):
         self._clonk()
      print()

   def queue_add( self, *x ):
      "add arguments (strings) to the list of task names that "\
         "might generate statuses."
      if not x:
         return
      prns = [ ( len( ind + ": " + fn ), task_start( ind + ": " ) + fn ) \
               for ( fn, ind ) \
               in  zip( x,
                        islice( cycle(indices), len( self._queue ), None )
                       )
              ]
      self._commands += [( self._queue_update_info, prns )]
      self._queue += x
      self._follow_commands()

   def activity( self, pid, number ):
      "'number' might be counting lines of output from an external program."
      self._preamble_once()
      tn = self._map( pid )
      self._acts[ tn ] += number

   def begin( self, pid, taskname ):
      """associates taskname and pid.
      
      there is no direct support for one pid switching between several tasks,
      other than calling begin again for every switch."""
      self._enqueue_command( pid, taskname, command = self._set_newtask )
      
   def success( self, pid ):
      self._enqueue_command( pid, yes )
   def done_with_warnings( self, pid ):
      self._enqueue_command( pid, maybe )
   def failed( self, pid ):
      self._enqueue_command( pid, no )
   def skipped( self, pid ):
      self._enqueue_command( pid, skip )
   def refresh( self ):
      self._enqueue_command( command = self._refresh_running )


def good_col_width( *widths ):
   "found by some arbitrary method. Takes widths as numbers."
   # måske noget med standardafvigelse ... ?

   bins =  sorted( list( set( widths ) ) )
   relevant_bins = bins[ -floor( len( bins ) / 2 ) : ][-3:]
   #                     ^ must be in uppper half      ^ and then the last ≤3
   # don't get fooled by shorter results:
   try:
      return relevant_bins[-1] if relevant_bins[-1] < relevant_bins[0] + 3 \
         else relevant_bins[0] + 1
   except IndexError:
      # probably got called with no arguments
      return shutil.get_terminal_size().columns
   
def print_columnized( *prns ):
   "each prn in prns is a tuple ( <printed width>, <string to print> )"
   
   w = good_col_width( *(prn[0] for prn in prns) )
   if shutil.get_terminal_size().columns < w * 2 :
      for prn in prns:
         print( prn[1] )
   else:
      # cache, and also keep fixed for duration of output:
      term_width = shutil.get_terminal_size().columns
      line_length = 0
      
      for prn in prns:
         spacer_length = ceil( line_length / w ) * w - line_length
         print_length = prn[0]
         if line_length \
               and spacer_length + print_length + line_length > term_width:
            print()
            spacer_length = line_length = 0
         print( " " * spacer_length, end="" )
         print( prn[1], end = "" )
         line_length += spacer_length + print_length
      print()
   return prns

class PoolOutputManager( SyncManager ):
   pass

PoolOutputManager.register( "PoolOutput", PoolOutput )
