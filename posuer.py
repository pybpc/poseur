# -*- coding: utf-8 -*-

import argparse
import functools
import glob
import locale
import os
import re
import shutil
import sys
import uuid

import parso
import tbtrim

__all__ = ['posuer', 'convert']

# multiprocessing may not be supported
try:        # try first
    import multiprocessing
except ImportError:  # pragma: no cover
    multiprocessing = None
else:       # CPU number if multiprocessing supported
    if os.name == 'posix' and 'SC_NPROCESSORS_CONF' in os.sysconf_names:  # pragma: no cover
        CPU_CNT = os.sysconf('SC_NPROCESSORS_CONF')
    elif 'sched_getaffinity' in os.__all__:  # pragma: no cover
        CPU_CNT = len(os.sched_getaffinity(0))  # pylint: disable=E1101
    else:  # pragma: no cover
        CPU_CNT = os.cpu_count() or 1
finally:    # alias and aftermath
    mp = multiprocessing
    del multiprocessing

# version string
__version__ = '0.1.0.dev1'

# from configparser
BOOLEAN_STATES = {'1': True, '0': False,
                  'yes': True, 'no': False,
                  'true': True, 'false': False,
                  'on': True, 'off': False}

# environs
LOCALE_ENCODING = locale.getpreferredencoding(False)

# macros
grammar_regex = re.compile(r"grammar(\d)(\d)\.txt")
POSUER_VERSION = sorted(filter(lambda version: version >= '3.8',  # when Python starts to have positional-only arguments
                               map(lambda path: '%s.%s' % grammar_regex.match(os.path.split(path)[1]).groups(),
                                   glob.glob(os.path.join(parso.__path__[0], 'python', 'grammar??.txt')))))
del grammar_regex


class ConvertError(SyntaxError):
    pass

###############################################################################
# Traceback trim (tbtrim)


# root path
ROOT = os.path.dirname(os.path.realpath(__file__))


def predicate(filename):  # pragma: no cover
    if os.path.basename(filename) == 'posuer':
        return True
    return (ROOT in os.path.realpath(filename))


tbtrim.set_trim_rule(predicate, strict=True, target=ConvertError)

###############################################################################
# Positional-only decorator


def decorator(*posuer):
    def caller(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            pass
        return wrapper
    return caller


###############################################################################
# Main convertion implementation


def convert(string, source='<unknown>'):
    """The main conversion process.

    Args:
     - string -- str, context to be converted
     - source -- str, source of the context

    Envs:
     - POSUER_VERSION -- convert against Python version (same as `--python` option in CLI)
     - POSUER_DISMISS -- dismiss runtime checks for positional-only arguments (same as `--dismiss` option in CLI)

    Returns:
     - str -- converted string

    """
    POSUER_DISMISS = BOOLEAN_STATES.get(os.getenv('POSUER_DISMISS', '0').casefold(), False)

    def parse(string, error_recovery=False):
        try:
            return parso.parse(string, error_recovery=error_recovery,
                               version=os.getenv('POSUER_VERSION', POSUER_VERSION[-1]))
        except parso.ParserSyntaxError as error:
            message = '%s: <%s: %r> from %s' % (error.message, error.error_leaf.token_type,
                                                error.error_leaf.value, source)
            raise ConvertError(message).with_traceback(error.__traceback__)


    def decorate(node):
        pass


    def dismiss(node):
        string = ''

        # <Operator: (>
        string += '('

        params = ''
        poflag = False
        for child in node.children[1:-1]:
            if child.type == 'operator' and child.value == '/':
                poflag = True
                params += child.get_code().replace('/', '')
            elif poflag and child.type == 'operator' and child.value == ',':
                pass
            else:
                params += child.get_code()
        string += re.sub(r'(^\s*,\s*)|(\s*,\s*)$', r'', params)

        # <Operator: )>
        string += ')'

        return string


    def walk(node):
        string = ''

        if node.type == 'funcdef':
            if not POSUER_DISMISS:
                string += decorate(node)
            for child in node:
                if child.type == 'parameters':
                    string += dismiss(child)
                else:
                    string += node.get_code()
            return string

        if isinstance(node, parso.python.tree.PythonLeaf):
            string += node.get_code()

        if hasattr(node, 'children'):
            for child in node.children:
                string += walk(child)

        return string

    # parse source string
    module = parse(string)

    # convert source string
    string = walk(module)

    # return converted string
    return string


def posuer(filename):
    """Wrapper works for conversion.

    Args:
     - filename -- str, file to be converted

    Envs:
     - POSUER_QUIET -- run in quiet mode (same as `--quiet` option in CLI)
     - POSUER_ENCODING -- encoding to open source files (same as `--encoding` option in CLI)
     - POSUER_VERSION -- convert against Python version (same as `--python` option in CLI)
     - POSUER_DISMISS -- dismiss runtime checks for positional-only arguments (same as `--dismiss` option in CLI)

    """
    POSUER_QUIET = BOOLEAN_STATES.get(os.getenv('POSUER_QUIET', '0').casefold(), False)
    if not POSUER_QUIET:
        print('Now converting %r...' % filename)

    # fetch encoding
    encoding = os.getenv('POSUER_ENCODING', LOCALE_ENCODING)

    # file content
    with open(filename, 'r', encoding=encoding) as file:
        text = file.read()

    # do the dirty things
    text = convert(text, filename)

    # dump back to the file
    with open(filename, 'w', encoding=encoding) as file:
        file.write(text)


###############################################################################
# CLI & entry point

# default values
__cwd__ = os.getcwd()
__archive__ = os.path.join(__cwd__, 'archive')
__posuer_version__ = os.getenv('POSUER_VERSION', POSUER_VERSION[-1])
__posuer_encoding__ = os.getenv('POSUER_ENCODING', LOCALE_ENCODING)


def get_parser():
    parser = argparse.ArgumentParser(prog='posuer',
                                     usage='posuer [options] <python source files and folders...>',
                                     description='Back-port compiler for Python 3.8 positional-only parameters.')
    parser.add_argument('-V', '--version', action='version', version=__version__)
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='run in quiet mode')

    archive_group = parser.add_argument_group(title='archive options',
                                              description="duplicate original files in case there's any issue")
    archive_group.add_argument('-n', '--no-archive', action='store_true',
                               help='do not archive original files')
    archive_group.add_argument('-p', '--archive-path', action='store', default=__archive__, metavar='PATH',
                               help='path to archive original files (%s)' % __archive__)

    convert_group = parser.add_argument_group(title='convert options',
                                              description='compatibility configuration for none-unicode files')
    convert_group.add_argument('-c', '--encoding', action='store', default=__posuer_encoding__, metavar='CODING',
                               help='encoding to open source files (%s)' % __posuer_encoding__)
    convert_group.add_argument('-v', '--python', action='store', metavar='VERSION',
                               default=__posuer_version__, choices=POSUER_VERSION,
                               help='convert against Python version (%s)' % __posuer_version__)
    convert_group.add_argument('-d', '--dismiss', action='store_true',
                               help='dismiss runtime checks for positional-only parameters')

    parser.add_argument('file', nargs='+', metavar='SOURCE', default=__cwd__,
                        help='python source files and folders to be converted (%s)' % __cwd__)

    return parser


def main(argv=None):
    """Entry point for posuer."""
    parser = get_parser()
    args = parser.parse_args(argv)

    # set up variables
    ARCHIVE = args.archive_path
    archive = (not args.no_archive)
    os.environ['POSUER_VERSION'] = args.python
    os.environ['POSUER_ENCODING'] = args.encoding
    POSUER_QUIET = os.getenv('POSUER_QUIET')
    os.environ['POSUER_QUIET'] = '1' if args.quiet else ('0' if POSUER_QUIET is None else POSUER_QUIET)
    POSUER_DISMISS = os.getenv('POSUER_DISMISS')
    os.environ['POSUER_DISMISS'] = '1' if args.dismiss else ('0' if POSUER_DISMISS is None else POSUER_DISMISS)

    def find(root):  # pragma: no cover
        """Recursively find all files under root."""
        flst = list()
        temp = os.listdir(root)
        for file in temp:
            path = os.path.join(root, file)
            if os.path.isdir(path):
                flst.extend(find(path))
            elif os.path.isfile(path):
                flst.append(path)
            elif os.path.islink(path):  # exclude symbolic links
                continue
        yield from flst

    def rename(path):
        stem, ext = os.path.splitext(path)
        name = '%s-%s%s' % (stem, uuid.uuid4(), ext)
        return os.path.join(ARCHIVE, name)

    # make archive directory
    if archive:
        os.makedirs(ARCHIVE, exist_ok=True)

    # fetch file list
    filelist = list()
    for path in args.file:
        if os.path.isfile(path):
            if archive:
                dest = rename(path)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy(path, dest)
            filelist.append(path)
        if os.path.isdir(path):
            if archive:
                shutil.copytree(path, rename(path))
            filelist.extend(find(path))

    # check if file is Python source code
    ispy = lambda file: (os.path.isfile(file) and (os.path.splitext(file)[1] in ('.py', '.pyw')))
    filelist = sorted(filter(ispy, filelist))

    # if no file supplied
    if len(filelist) == 0:
        parser.error('argument PATH: no valid source file found')

    # process files
    if mp is None or CPU_CNT <= 1:
        [posuer(filename) for filename in filelist]  # pragma: no cover
    else:
        mp.Pool(processes=CPU_CNT).map(posuer, filelist)


if __name__ == '__main__':
    sys.exit(main())
