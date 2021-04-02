======
poseur
======

------------------------------------------------------------------
back-port compiler for Python 3.8 positional-only parameter syntax
------------------------------------------------------------------

:Version: v0.4.3
:Date: April 03, 2021
:Manual section: 1
:Author:
    Contributors of the Python Backport Compiler project.
    See https://github.com/pybpc
:Copyright:
    *poseur* is licensed under the **MIT License**.

SYNOPSIS
========

poseur [*options*] <*Python source files and directories*> ...

DESCRIPTION
===========

Since PEP 570, Python introduced *positional-only parameters* syntax in
version __3.8__. For those who wish to use *positional-only parameters* in
their codes, `poseur` provides an intelligent, yet imperfect, solution of
a **backport compiler** by removing *positional-only parameters* syntax
whilst introduce a *decorator* for runtime checks, which guarantees you to
always write *positional-only parameters* in Python 3.8 flavour then compile
for compatibility later.

This man page mainly introduces the CLI options of the ``poseur`` program.
You can also checkout the online documentation at
https://bpc-poseur.readthedocs.io/ for more details.

OPTIONS
=======

positional arguments
--------------------

:SOURCE:                Python source files and directories to be converted

optional arguments
------------------

-h, --help              show this help message and exit
-V, --version           show program's version number and exit
-q, --quiet             run in quiet mode

-C *N*, --concurrency *N*
                        the number of concurrent processes for conversion

--dry-run               list the files to be converted without actually performing conversion and archiving

-s *[FILE]*, --simple *[FILE]*
                        this option tells the program to operate in "simple mode"; if a file name is provided, the program will convert
                        the file but print conversion result to standard output instead of overwriting the file; if no file names are
                        provided, read code for conversion from standard input and print conversion result to standard output; in
                        "simple mode", no file names shall be provided via positional arguments

archive options
---------------

backup original files in case there're any issues

-na, --no-archive       do not archive original files

-k *PATH*, --archive-path *PATH*
                        path to archive original files

-r *ARCHIVE_FILE*, --recover *ARCHIVE_FILE*
                        recover files from a given archive file

-r2                     remove the archive file after recovery
-r3                     remove the archive file after recovery, and remove the archive directory if it becomes empty

convert options
---------------

conversion configuration

-vs *VERSION*, --vf *VERSION*, --source-version *VERSION*, --from-version *VERSION*
                        parse source code as this Python version

-l *LINESEP*, --linesep *LINESEP*
                        line separator (**LF**, **CRLF**, **CR**) to read source files

-t *INDENT*, --indentation *INDENT*
                        code indentation style, specify an integer for the number of spaces, or ``'t'``/``'tab'`` for tabs

-n8, --no-pep8          do not make code insertion **PEP 8** compliant
-nr, --dismiss-runtime  dismiss runtime checks for positional-only parameters

-d *NAME*, --decorator-name *NAME*
                        name of decorator for runtime checks

ENVIRONMENT
===========

``poseur`` currently supports two environment variables.

:POSEUR_QUIET:          run in quiet mode
:POSEUR_CONCURRENCY:    the number of concurrent processes for conversion
:POSEUR_DO_ARCHIVE:     whether to perform archiving
:POSEUR_ARCHIVE_PATH:   path to archive original files
:POSEUR_SOURCE_VERSION: parse source code as this Python version
:POSEUR_LINESEP:        line separator to read source files
:POSEUR_INDENTATION:    code indentation style
:POSEUR_PEP8:           whether to make code insertion **PEP 8** compliant
:POSEUR_DISMISS:        dismiss runtime checks for positional-only arguments
:POSEUR_DECORATOR:      name of decorator for runtime checks

SEE ALSO
========

pybpc(1), f2format(1), walrus(1), vermin(1)
