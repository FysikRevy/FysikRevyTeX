# coding: utf-8
import os
import shutil
import subprocess
import tempfile
import uuid
from os import getpid
from multiprocessing import Pool, cpu_count, ProcessError
from time import time,sleep
from pathlib import Path
from itertools import takewhile, cycle, zip_longest
from traceback import format_exception
from subprocess import TimeoutExpired

from config import configuration as conf
from pool_output import \
    PoolOutputManager, Output, text_effect, \
    print_columnized, indices, task_start
import excom

# fordi https://learn.microsoft.com/en-us/windows/security/threat-protection/security-policy-settings/create-symbolic-links
# tak, windows.
try:
    import _winapi
    def portable_dir_link( source, target ):
        _winapi.CreateJunction( source, target )
except ImportError:
    def portable_dir_link( source, target ):
        os.symlink( source, target )

class ConversionError( Exception ):
    pass
class CACHE:
    pass

def tex_type_dispatch( file_func, iter_func, skip_func,
                       tex, pdfname="", outputdir="", conf=conf
                      ):
    """Choose among provided functions according to type of argument
tex, and whether or not the source file is newer than the
destination file, unless overridden in conf."""

    def deduce_paths( tex_path=None ):
        try:
            dir_offset = tex_path.parent.relative_to( Path.cwd() )
        except (ValueError, AttributeError):
            # not subpath, wasn't path
            dir_offset = Path()
    
        tex_cache = Path( conf["Paths"]["tex cache"] ) / dir_offset
        tex_cache.mkdir( parents = True, exist_ok = True )

        if not outputdir:
            try:
                od = conf["Paths"]["pdf"]
            except KeyError:
                od = "pdf"
        else:
            od = outputdir
        od = Path( od ) / dir_offset if outputdir != CACHE else tex_cache
        
        try:
            target_file = od / ( pdfname or tex_path.stem + ".pdf" )
        except AttributeError:
            raise ValueError( "pdfname is required when TeX'ing an object "
                              "with no assocated file name.", tex
                             )

        return target_file, tex_cache

    def shouldnt_skip ( src_mod, target ):
        force = conf.conf.getboolean( "TeXing", "force TeXing of all files" )
        try:
            return force or src_mod > target.stat().st_mtime
        except KeyError:
            # set default
            conf["TeXing"]["force TeXing of all files"] = "no"
            return shouldnt_skip( src_mod, target )
        except FileNotFoundError:
            return True

    match tex:
        case Path( fn ) | str( fn ) if fn[-4:] == ".tex":
            # path to a TeX file
            sa = Path( tex ).resolve()
            target_pdf, tex_cache = deduce_paths( sa )
            picked_func = file_func if \
                shouldnt_skip( sa.stat().st_mtime, target_pdf )\
                else skip_func

        case str():
            # raw TeX code
            sa = ( x for x in [ tex ] )
            target_pdf, tex_cache = deduce_paths()
            picked_func = iter_func

        case tex if type( tex ).__name__ == "TeX":
            sa = ( x for x in tex )
            target_pdf, tex_cache = deduce_paths(
                Path( tex.fname ).resolve() if tex.fname else None
            )
            picked_func = iter_func if \
                shouldnt_skip( tex.info[ "modification_time" ], target_pdf ) \
                else skip_func

        case tex if type( tex ).__name__ == "Material":
            sa = Path( tex.path ).resolve()
            target_pdf, tex_cache = deduce_paths( sa )
            picked_func = file_func if \
                shouldnt_skip( tex.modification_time, target_pdf )\
                else skip_func

        case _:
            raise TypeError("Input should be either TeX code, a string of a "
                            ".tex file, a TeX object or a Material object.")

    return picked_func( sa, target_pdf=target_pdf, cache_dir=tex_cache )

def task_name( file_path ):
    # class Material
    try:
        return Path( file_path.path ).name
    except AttributeError:
        pass
    # class TeX
    try:
        return file_path.fname
    except AttributeError:
        pass
    # class Path
    try:
        return str( file_path.relative_to( Path.cwd() ) )
    except ValueError:
        # not subpath
        try:
            return file_path.name
        except AttributeError:
            pass
    except AttributeError:
        pass
    # string
    return file_path

def tex_to_pdf( tex, pdfname="", outputdir="", repetitions=2,
              encoding='utf-8', output=Output(), conf=conf
             ):

    task = pdfname or task_name( tex )
    output.begin( getpid(), task )

    class SkipSignal( Exception ):
        pass

    def call_tex( fn, cache_dir, cdir=None ):
        for _ in range(repetitions):
            with excom.TeXProcess( fn,
                                   outputname = pdfname or None,
                                   cachedir = cache_dir,
                                   cdir = cdir,
                                   encoding = encoding
                                  ) as tex_proc:
                for o,e in tex_proc:
                    if o:
                        output.activity( getpid(),
                                         sum( 1 for c in o if c == "\n" )
                                        )
                        # output loads and break things
                        if conf.conf.getboolean(
                                "TeXing", "verbose output"
                        ):
                            print( o )
                t = tex_proc
        return t

    def tex_file( tex, target_pdf, cache_dir ):
        return ( target_pdf, cache_dir, call_tex( tex, cache_dir ) )

    def tex_iter( tex_iterator, target_pdf, cache_dir ):
        with tempfile.NamedTemporaryFile(
                delete_on_close=False,
                mode="wt",
                encoding=encoding,
                suffix=".tex"
        ) as temp:
            try:
                # bagudkompatibilitet
                portable_dir_link( str( Path.cwd() ),
                                   str( Path.cwd() / "src_dir" )
                                  )
            except:
                pass
            for t in tex_iterator:
                temp.write( t )
            temp.close()
            return ( target_pdf,
                     cache_dir,
                     call_tex( temp.name, cache_dir=cache_dir, cdir=Path.cwd() )
                    )

    def tex_skip( tex, target_pdf, cache_dir ):
        raise SkipSignal( target_pdf )

    try:
        target_pdf, cache_dir, tex_proc = \
            tex_type_dispatch( tex_file, tex_iter, tex_skip,
                               tex, pdfname, outputdir, conf
                              )
        target_pdf.parent.mkdir( parents=True, exist_ok=True )
        ( cache_dir / target_pdf.name ).replace( target_pdf )
    except SkipSignal as skip:
        output.skipped( getpid() )
        return ( None, skip.args[0].name )
    except Exception as e:
        output.failed( getpid() )
        return ( ConversionError() if isinstance( e, FileNotFoundError ) \
                    else "".join( format_exception( e ) )
                 , task
                )

    if tex_proc.returncode == 0:
        output.success( getpid() )
    else:
        output.done_with_warnings( getpid() )
    return ( tex_proc.returncode, task )

def tex_to_wordcount( tex, output=Output(), conf=conf,
                      outputname=None, encoding="utf-8" ):
    task = outputname or task_name( tex )
    output.begin( getpid(), task )

    class SkipSignal( Exception ):
        pass

    def tex_file( tex, target_pdf, cache_dir ):
        outputname = Path( target_pdf ).stem
        def handle_output( o ):
            output.activity( getpid(), sum( 1 for c in o if c == "\n" ) )
            # output loads and break things
            if conf.conf.getboolean( "TeXing", "verbose output" ):
                print( o )

        with excom.TeXProcess( "scripts/revywordcount.tex",
                               outputname = outputname,
                               cachedir = cache_dir,
                               cdir = Path.cwd(),
                               interactive = True,
                               encoding = encoding
                              ) as tex_proc:
            try:
                o,e = tex_proc.communicate( input=str(tex), timeout=1 )
            except TimeoutExpired:
                pass
            else:
                handle_output( o )

            for o,e in tex_proc:
                handle_output( o )

            return ( cache_dir / ( outputname + ".log" ), tex_proc )

    def iter_tex( tex_iterator, target_pdf, cache_dir ):
        with tempfile.NamedTemporaryFile(
                delete_on_close=False,
                mode="wt",
                encoding=encoding,
                suffix=".tex"
        ) as temp:
            try:
                # bagudkompatibilitet
                portable_dir_link( str( Path.cwd() ),
                                   str( Path.cwd() / "src_dir" )
                                  )
            except:
                pass
            for t in tex_iterator:
                temp.write( t )
            temp.close()
            return tex_file( temp.name, target_pdf, cache_dir )

    def skip_tex( tex, target_pdf, cache_dir ):
        raise SkipSignal( target_pdf )

    try:
        out_file, tex_proc = tex_type_dispatch(
            tex_file, iter_tex, skip_tex, tex,
            pdfname = Path( task ).stem + "-wc.log",
            outputdir = CACHE,
            conf=conf
        )
    except SkipSignal as skip:
        out_file = skip.args[0]
        queued_output = output.skipped
        rc = None
    except Exception as e:
        output.failed( getpid() )
        return "".join( format_exception( e ) ), {}
    else:
        queued_output = output.success if tex_proc.returncode == 0\
            else output.done_with_warnings
        rc = tex_proc.returncode

    try:
        ( out_file.parent / ( out_file.stem + ".pdf" ) ).unlink()
    except:
        pass

    counts = {}
    try:
        with out_file.open() as f:

            def type_dispatch( line ):
                if "3.08641" in line:
                    return start_counting( "sung" )
                if "3.08643" in line:
                    return start_counting( "spoken" )

            def start_counting( linetype ):
                role = "".join(
                    [ line[-2:-1] for line
                      in takewhile(
                          lambda line: not "\\3.08632 :" in line\
                                   and not "\\3.08632 (" in line,
                          f
                      )
                      if "\\3.08632" in line
                     ]
                )
                if not role in counts:
                    counts[role] = {"spoken": 0, "sung": 0}
                for line in f:
                    if "3.08633" in line or "3.08635" in line:
                        counts[role][linetype] += 1
                    if "3.0864" in line:
                        return type_dispatch( line )

            for line in f:
                type_dispatch( line )
                output.activity( getpid(), 1 )

    except Exception as e:
        output.failed( getpid() )
        return "".join( format_exception( e ) ), counts
    queued_output( getpid() )
    return rc, counts

def parallel_tex_to_pdf( file_list,
                         outputdir    = "",
                         repetitions  = 2,
                         encoding     = 'utf-8',
                         conf         = conf
                        ):

    default_args = [ None, None, outputdir, repetitions, encoding ]
    new_file_list = [
        [ el, "" ] + default_args[2:] if isinstance( el, str )
        else list( el ) + default_args[ len( el ) : ]
        for el in file_list
    ]

    with Pool(processes = cpu_count()) as pool,\
         PoolOutputManager() as man:
        po = man.PoolOutput( cpu_count() )
        po.queue_add( *( a[1] if a[1] else task_name( a[0] )
                         for a in new_file_list
                        )
                     )
        new_file_list = [ f + [ po, conf ] for f in new_file_list ]
        result = pool.starmap_async( tex_to_pdf, new_file_list)
        while not result.ready():
            sleep( 1 )
            po.refresh()
        po.end_output()
        rs = result.get()
    fail, fail_other, err, done, skip = [],[],[],[],[]
    for ind,r in zip( cycle( indices ), rs ):
        ro = [ (ind,) + r ]
        match r[0]:
            case None:
                skip += ro
            case 0:
                done += ro
            case int():
                err += ro
            case ConversionError():
                fail += ro
            case _:
                fail_other += ro
    if fail:
        print( "\nFølgende filer kunne ikke produceres pga. "\
               + text_effect( "LaTeX-fejl", "error" )\
               + ":" )
        print_columnized( *(
            ( len( f ) + 3, task_start( i + ": " ) + f )
            for i,_,f in fail
        ))
    if fail_other:
        print( "\nFølgende filer kunne ikke produceres pgs. "\
               + text_effect( "ikke-LaTeX-fejl", "error" ) + "." )
        for i,e,f in fail_other:
            print( task_start( i + ": " ) + f )
            print( e, end="" )
    if err:
        print( "\nFølgende filer kunne TeX'es, men med "\
               + text_effect( "advarsler", "warn" ) + ":"
              )
        print_columnized( *(
            ( len( f ) + 3, task_start( i + ": " ) + f )
            for i,_,f in err
        ))
    print()
    if done:
        print( ( "{} filer blev " \
                 + text_effect( "korrekt TeX'et", "success" ) + "."
                ).format( len( done ))
              )
    if skip:
        print( ("{} filer havde ingen opdateringer, og blev "\
                + text_effect( "sprunget over", "skip" ) + "."
                ).format( len( skip ))
              )
    if fail or fail_other:
        raise ProcessError()
    return rs

class Converter:
    def __init__(self):
        self.conf = conf

    def textopdf(self, *args, **kwargs):
        """
        Dummy wrapper method to make multiprocessing work on a 
        decorated function.
        """
        return tex_to_pdf(*args, conf=self.conf, **kwargs)

    def task_name( self, file_path ):
        return task_name( file_path )
    
    def parallel_textopdf(self, file_list, outputdir="", repetitions=2, encoding='utf-8'):
        return parallel_tex_to_pdf(
            file_list, outputdir, repetitions, encoding, self.conf
        )

    def tex_to_wordcount(self, tex_file, output=Output(), conf=None ):
        return tex_to_wordcount( tex_file, output, conf or self.conf )
