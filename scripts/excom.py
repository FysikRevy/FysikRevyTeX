#  coding; utf-8

import os, subprocess
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

def tex( texfile, outputname=None, searchdir=None ):
   texinputs = ":".join( path.as_posix + "/" for path
                         in ( Path( texfile ).parent,
                              Path( searchdir )
                             )
                         if path != None
                        ) + ":"
   try:
      texinputs += os.environ["TEXINPUTS"]
   except KeyError:
      pass
   env = { **os.environ, **{"TEXINPUTS": texinputs } }
   jobname = [ "-job-name=" + str( Path( outputname ).stem ) ]\
      if outputname else []

   return PopenGen(
      [ conf["TeXing"]["tex command"], "-interaction=nonstopmode" ]\
        + jobname + [ str( texfile ) ],
      env = env,
      stdout = subprocess.PIPE,
      stderr = subprocess.STDOUT,
      text = True
   )

