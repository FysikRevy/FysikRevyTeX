#  coding; utf-8
import os
import uuid
from asyncio import create_subprocess_exec, new_event_loop, subprocess, timeout
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

class TeXProcess():
   def __init__( self, texfile, cdir=None, cachedir=None, outputname=None,
                 searchdirs=None, interactive=None, encoding="utf-8"
                ):
      if isinstance( searchdirs, str ):
         raise TypeError( "searchdirs must be an iterable of directories. "
                          "Got {}".format( searchdirs )
                         )
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

         self.job_name = [ "-jobname=" ]
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

      self.searchdirs = [ cdir / d for d in ( searchdirs or [] ) ]
      self.runmode = [ "-interaction=nonstopmode" ] if not interactive\
          else []
      self.encoding = encoding

   def __enter__( self ):
      # TODO: testet på Windows, ikke på POSIX
      if self.searchdirs:
         sl = os.pathsep.join( str( d ) for d in self.searchdirs )
         try:
            texinputs = os.pathsep.join(( sl, os.environ["TEXINPUTS"], "" ))
         except KeyError:
            texinputs = sl + os.pathsep
         env = { **os.environ, **{"TEXINPUTS": texinputs} }
      else:
         env = None

      subproc = create_subprocess_exec(
         *[ conf["TeXing"]["tex command"] ] \
            + self.runmode \
            + self.job_name \
            + [ str( self.texfile ) ],
         cwd = str( self.exec_dir ),
         env = env,
         stdin = subprocess.PIPE,
         stdout = subprocess.PIPE,
         stderr = subprocess.STDOUT,
         text = False
      )

      class ProcOut:
         def __iter__( ss ):
             async def try_read():
                 self.p = await subproc
                 while self.p.returncode == None:
                     try:
                         async with timeout(1):
                             yield await self.p.stdout.readline()
                     except TimeoutError:
                         continue
                 ss.returncode = self.p.returncode

             loop = new_event_loop()
             reader = try_read()
             while True:
                 try:
                     yield loop.run_until_complete( reader.__anext__() )\
                               .decode('utf-8')
                 except StopAsyncIteration:
                     break
                 except UnicodeDecodeError:
                     yield ""

      return ProcOut()

   def __exit__( self, *_ ):
      try:
         self.p.terminate()
         self.cache_link.unlink()
      except:
         pass
