#  coding; utf-8

import os, subprocess, uuid
from pathlib import Path

from config import configuration as conf

# fordi https://learn.microsoft.com/en-us/windows/security/threat-protection/security-policy-settings/create-symbolic-links
# tak, windows.
try:
    import _winapi
    def portable_dir_link( source, target ):
        _winapi.CreateJunction( source, target )
except ImportError:
    def portable_dir_link( source, target ):
        os.symlink( source, target )

class PopenGen( subprocess.Popen ):
   def __iter__( self ):
      while True:
         try:
            yield self.communicate( timeout = .2 )
         except subprocess.TimeoutExpired:
            yield "",""
         if self.returncode != None:
            return

class TeXProcess():
   def __init__( self, texfile, cachedir=None,
                 outputname=None, searchdirs=None
                 ):
      try:
         conf["TeXing"]["tex command"]
      except KeyError:
         conf["TeXing"]["tex command"] = "pdflatex"

      self.texfile = Path( texfile )
      self.src_dir = self.texfile.resolve().parent
      dst_dir = Path( cachedir ).resolve() if cachedir else self.src_dir
      if self.src_dir == dst_dir and outputname == None:
         self.jobname = []
      else:
         dst_dir.mkdir( parents=True, exist_ok=True )
         try:
            jobdir = dst_dir.relative_to( self.src_dir )
         except ValueError:               # not subpath
            self.cache_link = self.src_dir / Path( str( uuid.uuid4()))
            portable_dir_link( str( dst_dir ), str( self.cache_link ) )
            jobdir = self.cache_link.relative_to( self.src_dir )
         self.jobname = [ "-job-name={}".format(
            jobdir / ( Path( outputname ).stem if outputname
                       else Path( texfile ).stem
                      )
         )]
      self.searchdirs = searchdirs

   def __enter__( self ):
      # TODO: testet på Windows, ikke på POSIX
      if self.searchdirs:
         sl = ";".join( str( Path( d ).resolve() ) for d in self.searchdirs )
         try:
            texinputs = ";".join(( sl, os.environ["TEXINPUTS"], "" ))
         except KeyError:
            texinputs = sl + ";"
         env = { **os.environ, **{"TEXINPUTS": texinputs} }
      else:
         env = None

      self.p = PopenGen(
         [ conf["TeXing"]["tex command"], "-interaction=nonstopmode" ]\
         + self.jobname + [ str( self.texfile.name ) ],
         cwd = str( self.src_dir ),
         env = env,
         stdout = subprocess.PIPE,
         stderr = subprocess.STDOUT,
         text = True
      )
      return self.p

   def __exit__( self, *_ ):
      try:
         self.p.terminate()
         self.cache_link.unlink()
      except:
         pass
