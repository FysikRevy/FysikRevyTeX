import shutil
import time
from multiprocessing import Pool
from itertools import cycle
from math import ceil

headers = (  "Proces #{}"
            ,"Proc#{}"
            ,"Pr{}"
            ,"P{}"
            ,"{}"
            ,""
           )

indices = "abcdefghijklmnopqrstuvwxyzæøåABCDEFGHIJKLMNOPQRSTUVWXYZÆØÅ0123456789"
file_list_column_width = 24

class PoolOutput:
   def __init__( self, proc_count ):
      pass

def good_col_width( *widths ):
   "found by some arbitrary method. Takes widths as numbers."
   # måske noget med standardafvigelse ... ?

   bins = [x for x in sorted( list( set( *widths ) ) )]
   relevant_bins = bins[ -floor( len( bins ) / 2 ) : ][-3:]
   #                     ^ must be in uppper half      ^ and then the last ≤3
   # don't get fooled by shorter results:
   return relevant_bins[-1] if relevant_bins[-1] < relevant_bins[0] + 3 \
      else relevant_bins[0] + 1
   
def pt( proc_count ):
   cell_width = int( shutil.get_terminal_size().columns / proc_count )
   if cell_width < 3:
      raise NotImplementedError # TODO
   header_format = next(
      header for header in headers
      if len( header.format( proc_count ) ) < cell_width - 1
   )
   cell_format = "{:^" + str(cell_width - 1) + "}|"
   for p in range( proc_count ):
      print( cell_format.format( header_format.format( p + 1 ) ), end="" )
   print()

def prpid( _ ):
   print( os.getpid() )
   time.sleep(5)

def spin():
   with Pool() as p:
      p.map( prpid, [x for x in range(30)] )

if __name__ == "__main__":
   spin()

def list_queue( queue ):
   fns = [ args[1] for args in queue ]
   info_fmt = ( "\033[34m", "\033[0m" )
   len_info_fmt = sum( len( s ) for s in info_fmt )
   prns = [ info_fmt[0] + ind + ": " + info_fmt[1] + fn \
            for ( fn, ind ) in zip( fns, cycle( indices )) ]

   w = good_col_width( len( prn ) - len_info_fmt for prn in prns )
   if shutil.get_terminal_size().columns < w * 2 :
      for prn in prns:
         print( prn )
   else:
      # cache, and also keep fixed for duration of output:
      term_width = shutil.get_terminal_size().columns
      line_length = 0
      
      for prn in prns:
         spacer_length = ceil( line_length / w ) * w - line_length
         print_length = len( prn ) - len_info_fmt
         if line_length \
               and spacer_length + print_length + line_length > term_width:
            print()
            spacer_length = line_length = 0
         print( " " * spacer_length, end="" )
         print( prn, end = "" )
         line_length += spacer_length + print_length
      print()
   return prns
