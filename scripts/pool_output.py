import shutil

headers = (  "Proces #{}"
            ,"Proc#{}"
            ,"Pr{}"
            ,"P{}"
            ,"{}"
            ,""
           )

class PoolOutput:
   def __init__( self, proc_count ):
      pass

def pt( proc_count ):
   cell_width = int( shutil.get_terminal_size().columns / proc_count )
   header_format = next(
      header for header in headers
      if len( header.format( proc_count ) ) < cell_width - 1
   )
   cell_format = "{:^" + str(cell_width - 1) + "}|"
   for p in range( proc_count ):
      print( cell_format.format( header_format.format( p + 1 ) ), end="" )
   print()
