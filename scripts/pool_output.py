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
            ,""
           )
indices = "abcdefghijklmnopqrstuvwxyzæøåABCDEFGHIJKLMNOPQRSTUVWXYZÆØÅ0123456789"
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
   sized_caches_defaults = (( "acts", 0 )
                           ,( "status", None )
                           )
   def __init__( self, n_processes, min_refresh_interval = 1 ):
      self.clonk_count = 0
      self.queue = tuple()
      self.n_processes = n_processes
      self.resize_caches( 0 )
      self.proc_map = dict()
      self.max_act_queue = [0] * 4
      self.bpm = min_refresh_interval
      self.refresh = self.refresh_running

   @property
   def n_processes( self ):
      return self._n

   @n_processes.setter
   def n_processes( self, x ):
      self._n = x
      self.cell_width = floor( shutil.get_terminal_size().columns / x )
      if self.cell_width < 3:
         raise NotImplementedError
      try:
         old_strs = self.strs
      except AttributeError:
         old_strs = []
      self.strs = [ s[ 1 - self.cell_width : ] for s in old_strs[:x] ]\
                   + [ "." * min( self.clonk_count, self.cell_width - 1 ) ]\
                     * ( x - len ( old_strs ) )

   def resize_caches( self, new_size ):
      # sized caches with defaults:
      for s in self.sized_caches_defaults:
         try:
            old = getattr( self, s[0] )
         except AttributeError:
            old = []
         setattr( self, s[0],
                  old[:new_size] + [ s[1] ] * ( new_size - len( old ) )
                 )

   def empty_caches( self ):
      for s in self.sized_caches_defaults:
         try:
            l = len( getattr( self, s[0] ) )
         except AttributeError:
            pass
         else:
            setattr( self, s[0], [ s[1] ] * l )

   def map( self, pid ):
      try:
         tn = self.proc_map[ pid ]
      except KeyError:
         tn = len( self.proc_map )
         self.proc_map[ pid ] = tn
         self.resize_caches( tn + 1 )

      return tn

   def map_drop( self, index ):
      self.proc_map = { pid: (i if i < index else i - 1) \
                        for pid, i in items( self.proc_map ) \
                        if i != index
                       }
      for s in self.sized_caches_default:
         old = getattr( self, s[0] )
         setattr( self, s[0], old[ : index ] + old[ index+1 : ] )

   def map_move( self, fr, to ):
      for s in self.sized_caches_default:
         old = getattr( self, s[0] )
         old[ to ] = old[ fr ]
         setattr( self, s[0], old )
      for pid in self.proc_map:
         if self.proc_map[ pid ] == to:
            self.map_drop( fr ) # probably breaks the iterator
            self.proc_map[ pid ] = fr
            break
      else:                     # nobreak
         # oh, dear ... maybe:
         raise IndexError(
            "proc_map has no entry pointing to index {}".format( to )
         )

   def queue_add( self, *x ):
      self.pause()
      print( "\n  Tilføjet til kø:" )
      prns = [ ( len( ind + ": " + fn ), task_start( ind + ": " ) + fn ) \
               for ( fn, ind ) \
               in  zip( x,
                        islice( cycle(indices), len( self.queue ), None )
                       )
              ]
      print_columnized( *prns )
      self.queue += x
      self.resume()

   def legend( self ):
      print( "  Multiprocesmonitor:" )
      print( "Nuværende opgave: {}".format( task_start( indices[0] ) ), end="" )
      print( ", aktivitet: " + indicators, end="" )
      print( ", resultat: {}{}{}{}".format( yes, maybe, no, skip ) )

   def proc_headers( self ):
      header_format = next(
         header for header in headers
         if len( header.format( self.n_processes ) ) < self.cell_width - 1
      )
      cell_format = "{:^" + str( self.cell_width - 1 ) + "}|"
      for p in range( self.n_processes ):
         print( cell_format.format( header_format.format( p + 1 ) ), end="" )
      print()

   def preamble_once( self ):
      print()
      self.legend()
      self.proc_headers()
      self.clonk_time = time()
      self.activity = self.activity_running
      self.set_status = self.set_status_running

   def activity( self, pid, number ):
      self.preamble_once()
      return self.activity( pid, taskname, number )

   def set_status( self, pid, status ):
      self.preamble_once()
      return self.set_status( pid, status )

   def activity_running( self, pid, number ):
      tn = self.map( pid )
      self.acts[ tn ] += number

   def set_status_running( self, pid, status ):
      tn = self.map( pid )
      if self.status[ tn ]:
         self.clonk()

      self.status[ tn ] = status

   def begin( self, pid, taskname ):
      try:
         self.set_status( pid, task_start(
            next( c for c,n in zip( cycle( indices ), self.queue ) \
                  if n == taskname
                 )
         ))
      except StopIteration:
         raise KeyError( "Unqueued taskname: '{}'".format( taskname ) )

   def success( self, pid ):
      self.set_status( pid, yes )

   def done_with_warnings( self, pid ):
      self.set_status( pid, maybe )

   def failed( self, pid ):
      self.set_status( pid, no )

   def skipped( self, pid ):
      self.set_status( pid, skip )

   def clonk( self ):
      # next line?
      if self.clonk_count >= self.cell_width - 1:
         print()
         self.strs = [ "" ] * len( self.strs )
         self.clonk_count = 0

      # decide which character to print
      self.max_act_queue = self.max_act_queue[1:] + [ max( self.acts or 0 ) ]
      max_act = max( self.max_act_queue ) or 1 # classic
      for i,s in enumerate( self.strs ):
         try:
            t = self.status[i]
         except IndexError:
            t = None
         if t:
            self.strs[i] += t
            continue
         try:
            a = self.acts[i]
         except IndexError:
            a = 0
         self.strs[i] += indicators[
            ceil( a / max_act * (len( indicators ) - 1 ))
         ]
      self.clonk_count += 1
      self.clonk_time = time()
      self.empty_caches()
      
      # try to keep up with pid change
      while len( self.proc_map ) > self.n_processes:
         try:
            inactive = next(
               i for i, a, t in zip( count(), self.acts, self.status )
               if not a and not t
            )
         except StopIteration:
            break
         else:
            self.map_move( self.n_processes, inactive )

      # pull the lever, clonk
      print( "\r", end="" )
      for s in self.strs[ : self.n_processes ]:
         print( s + " " * ( self.cell_width - self.clonk_count ), end="" )
         
   def pause( self ):
      self.refresh = lambda *_: None
   def resume( self ):
      self.refresh = self.refresh_running
      self.refresh()

   def refresh_running( self ):
      try:
         if time() - self.clonk_time >= self.bpm:
            self.clonk()
      except AttributeError:
         pass

   def end_output( self ):
      self.clonk()
      print()
      

def good_col_width( *widths ):
   "found by some arbitrary method. Takes widths as numbers."
   # måske noget med standardafvigelse ... ?

   bins =  sorted( list( set( widths ) ) )
   relevant_bins = bins[ -floor( len( bins ) / 2 ) : ][-3:]
   #                     ^ must be in uppper half      ^ and then the last ≤3
   # don't get fooled by shorter results:
   return relevant_bins[-1] if relevant_bins[-1] < relevant_bins[0] + 3 \
      else relevant_bins[0] + 1
   
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
