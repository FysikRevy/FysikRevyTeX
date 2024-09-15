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
   def __init__( self, texfile, cdir=None, cachedir=None,
                 outputname=None, searchdirs=None
                 ):
      if isinstance( searchdirs, str ):
         raise TypeError( "searchdirs must be an iterable of directories. "
                          "Got {}".format( searchdirs )
                         )
      try:
         conf["TeXing"]["tex command"]
      except KeyError:
         conf["TeXing"]["tex command"] = "pdflatex"

      texfile = Path( texfile )
      try:
         cdir = Path( cdir ).resolve()
         self.exec_dir = cdir
         self.texfile = self.exec_dir / texfile
      except TypeError:
         self.texfile = texfile.resolve()
         self.exec_dir = self.texfile.parent
         cdir = Path.cwd()

      if cachedir or outputname:
         try:
            jobdir = cdir / Path( cachedir )
         except TypeError:
            jobdir = cdir
         try:
            jobname = Path( outputname ).stem
         except TypeError:
            jobname = texfile.stem

         self.job_name = [ "-job-name=" ]
         try:
            self.job_name[0] += str(
               jobdir.relative_to( self.exec_dir ) / jobname
            )
         except ValueError:     # not subpath
            self.cache_link = self.exec_dir / Path( str( uuid.uuid4() ))
            portable_dir_link( str( jobdir ), str( self.cache_link ) )

            self.job_name[0] += str(
               self.cache_link.relative_to( self.exec_dir ) / jobname
            )
         else:
            self.job_name = []

      self.searchdirs = ( cdir / d for d in ( searchdirs or [] ) )

   def __enter__( self ):
      # TODO: testet på Windows, ikke på POSIX
      if self.searchdirs:
         sl = ";".join( str( d ) for d in self.searchdirs )
         try:
            texinputs = ";".join(( sl, os.environ["TEXINPUTS"], "" ))
         except KeyError:
            texinputs = sl + ";"
         env = { **os.environ, **{"TEXINPUTS": texinputs} }
      else:
         env = None

      self.p = PopenGen(
         [ conf["TeXing"]["tex command"], "-interaction=nonstopmode" ]\
         + self.job_name + [ str( self.texfile.name ) ],
         cwd = str( self.exec_dir ),
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
