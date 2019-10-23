======
poseur
======

------------------------------------------------------------------
back-port compiler for Python 3.8 positional-only parameter syntax
------------------------------------------------------------------

:Version: v0.3.1
:Date: October 24, 2019
:Manual section: 1
:Author:
    Jarry Shaw, a newbie programmer, is the author, owner and maintainer
    of *poseur*. Please contact me at *jarryshaw@icloud.com*.
:Copyright:
    *poseur* is licensed under the **MIT License**.

SYNOPSIS
========

poseur [*options*] <*python source files and folders*> ...

DESCRIPTION
===========

Since PEP 570, Python introduced *positional-only parameters* syntax in
version __3.8__. For those who wish to use *positional-only parameters* in
their codes, `poseur` provides an intelligent, yet imperfect, solution of
a **backport compiler** by removing *positional-only parameters* syntax
whilst introduce a *decorator* for runtime checks, which guarantees you to
always write *positional-only parameters* in Python 3.8 flavour then compile
for compatibility later.

OPTIONS
=======

positional arguments
--------------------

:SOURCE:              python source files and folders to be converted

optional arguments
------------------

-h, --help            show this help message and exit
-V, --version         show program's version number and exit
-q, --quiet           run in quiet mode

archive options
---------------

duplicate original files in case there's any issue

-na, --no-archive     do not archive original files

-p *PATH*, --archive-path *PATH*
                      path to archive original files

convert options
---------------

compatibility configuration for none-unicode files

-c *CODING*, --encoding *CODING*
                      encoding to open source files

-v *VERSION*, --python *VERSION*
                      convert against Python version

-s *SEP*, --linesep *SEP*
                      line separator to process source files

-d, --dismiss         dismiss runtime checks for positional-only parameters
-nl, --no-linting     do not lint converted codes

-r *VAR*, --decorator *VAR*
                      name of decorator for runtime checks (${DECORATOR})

ENVIRONMENT
===========

``poseur`` currently supports two environment variables.

:POSEUR_QUIET:        run in quiet mode
:POSEUR_ENCODING:     encoding to open source files
:POSEUR_VERSION:      convert against Python version
:POSEUR_LINESEP:       line separator to process source files
:POSEUR_DISMISS:      dismiss runtime checks for positional-only arguments
:POSEUR_LINTING:      lint converted codes
:POSEUR_DECORATOR:    name of decorator for runtime checks

SEE ALSO
========

babel(1), f2format(1), walrus(1), vermin(1)
