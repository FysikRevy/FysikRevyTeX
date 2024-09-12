#  coding; utf-8

import subprocess
from pathlib import Path

from config import configuration as conf

try:
   conf["TeXing"]["tex command"]
except KeyError:
   conf["TeXing"]["tex command"] = "pdflatex"

class PopenGen( subprocess.Popen ):
   def __iter__( self ):
      while True:
         try:
            yield self.communicate( timeout = .2 )
         except subprocess.TimeoutExpired:
            yield "",""
         if self.returncode != None:
            return

def tex( texfile, outputfile=None, auxdir=None, searchdir=None ):
   output_args = [ "-output-directory=" + str( Path( outputfile ).parent ),
                   "-job-name=" + str( Path( outputfile ).stem )
                  ] if outputfile else []
   dir_args = [ k + str( v ) for k,v in { "-aux-directory=": auxdir,
                                          "-include-directory=": searchdir
                                         }.items()
                if v
               ]

   return PopenGen(
      [ conf["TeXing"]["tex command"], "-interaction=nonstopmode" ]\
        + output_args + dir_args + [ texfile ],
      stdout = subprocess.PIPE,
      stderr = subprocess.STDOUT,
      text = True
   )

