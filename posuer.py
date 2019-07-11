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

__all__ = ['posuer', 'convert', 'decorator']

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


_decorator = '''\
def _posuer_decorator(*posuer):
    """Positional-only arguments runtime checker.

    Args:
     - str, name of positional-only arguments

    Refs:
     - https://mail.python.org/pipermail/python-ideas/2017-February/044888.html

    """
    import functools
    def caller(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for posuer_args in posuer:
                if posuer_args in kwargs:
                    raise TypeError('%s() got an unexpected keyword argument %r' % (func.__name__, posuer_args))
            return func(*args, **kwargs)
        return wrapper
    return caller
'''


def decorator(*posuer):
    """Positional-only arguments runtime checker.

    Args:
     - str, name of positional-only arguments

    Refs:
     - https://mail.python.org/pipermail/python-ideas/2017-February/044888.html

    """
    def caller(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for posuer_args in posuer:
                if posuer_args in kwargs:
                    raise TypeError('%s() got an unexpected keyword argument %r' % (func.__name__, posuer_args))
            return func(*args, **kwargs)
        return wrapper
    return caller


###############################################################################
# Main convertion implementation


def parse(string, source, error_recovery=False):
    """Parse source string.

    Args:
     - string -- str, context to be converted
     - source -- str, source of the context
     - error_recovery -- bool, see `parso.Grammar.parse` (default: `False`)

    Envs:
     - POSUER_VERSION -- convert against Python version (same as `--python` option in CLI)

    Returns:
     - parso.python.tree.Module -- parso AST

    Raises:
     - ConvertError -- when `parso.ParserSyntaxError` raised

    """
    try:
        return parso.parse(string, error_recovery=error_recovery,
                           version=os.getenv('POSUER_VERSION', POSUER_VERSION[-1]))
    except parso.ParserSyntaxError as error:
        message = '%s: <%s: %r> from %s' % (error.message, error.error_leaf.token_type,
                                            error.error_leaf.value, source)
        raise ConvertError(message).with_traceback(error.__traceback__) from None


def decorate_lambdef(parameters, lambdef):
    """Append posuer decorator to lambda definition.

    Args:
     - parameters -- list[parso.python.tree.Param], extracted positional-only arguments
     - lambdef -- str, converted lambda string

    Returns:
     - str -- decorated lambda definition

    """
    return '_posuer_decorator(%s)(%s)' % (', '.join(map(lambda param: repr(param.name.value), parameters)), lambdef)


def dismiss_lambdef(node):
    """Dismiss positional-only arguments syntax.

    Args:
     - node -- parso.python.tree.Lambda, AST of lambda parameters

    Envs:
     - POSUER_LINTING -- lint converted codes (same as `--linting` option in CLI)

    Returns:
     - str -- converted lambda definition

    """
    params = ''
    prefix = ''
    suffix = ''

    flag_1 = False
    flag_2 = False
    for child in node.children:
        # <Param: ...>
        if child.type == 'param':
            flag_1 = True
            params += child.get_code()
        # lambda parameters
        elif flag_1:
            # <Operator: />
            if child.type == 'operator' and child.value == '/':
                params += child.get_code().replace('/', '')
            # <Operator: :>
            elif child.type == 'operator' and child.value == ':':
                flag_1 = False
                flag_2 = True
                suffix += child.get_code()
            # <Operator: *> / <Operator: ,> / <Param: ...>
            else:
                params += child.get_code()
        # lambda suite
        elif flag_2:
            suffix += child.get_code()
        # lambda declration
        else:
            prefix += child.get_code()

    POSUER_LINTING = BOOLEAN_STATES.get(os.getenv('POSUER_LINTING', '0').casefold(), False)
    if POSUER_LINTING:
        params += ', '.join(filter(None, map(lambda s: s.strip(), params.split(','))))
    else:
        params += ','.join(filter(lambda s: s.strip(), params.split(',')))

    return (prefix + params + suffix)


def extract_lambdef(node):
    """Extract positional-only arguments from lambda definition.

    Args:
     - node -- parso.python.tree.Lambda, AST of lambda definition

    Returns:
     - list[parso.python.tree.Param] -- extracted positional-only arguments

    """
    pos_only = list()

    pos_temp = list()
    for child in node.children:
        if child.type == 'param':
            pos_temp.append(child)
        elif child.type == 'operator' and child.value == '/':
            pos_only.extend(pos_temp)
            break

    return pos_only


def decorate_funcdef(parameters, column, funcdef):
    """Append posuer decorator to function definition.

    Args:
     - parameters -- list[parso.python.tree.Param], extracted positional-only arguments
     - column -- int, indentation of function definition
     - funcdef -- str, converted function string

    Envs:
     - POSUER_LINSEP -- line separator to process source files (same as `--linsep` option in CLI)

    Returns:
     - str -- decorated function definition

    """
    return '%s@_posuer_decorator(%s)%s%s' % ('\t'.expandtabs(column),
                                             ', '.join(map(lambda param: repr(param.name.value), parameters)),
                                             os.getenv('POSUER_LINSEP', os.linesep),
                                             funcdef)


def dismiss_funcdef(node):
    """Dismiss positional-only arguments syntax.

    Args:
     - node -- parso.python.tree.PythonNode, AST of function parameters

    Envs:
     - POSUER_LINTING -- lint converted codes (same as `--linting` option in CLI)

    Returns:
     - str -- converted parameters string

    """
    string = ''

    # <Operator: (>
    string += '('

    params = ''
    for child in node.children[1:-1]:
        # <Operator: />
        if child.type == 'operator' and child.value == '/':
            poflag = True
            params += child.get_code().replace('/', '')
        elif child.type == 'param' and child.default is not None:
            walk_string, _ = walk(child.default)
            params += walk_string
        # <Operator: *> / <Operator: ,>
        else:
            params += child.get_code()

    POSUER_LINTING = BOOLEAN_STATES.get(os.getenv('POSUER_LINTING', '0').casefold(), False)
    if POSUER_LINTING:
        string += ', '.join(filter(None, map(lambda s: s.strip(), params.split(','))))
    else:
        string += ','.join(filter(lambda s: s.strip(), params.split(',')))

    # <Operator: )>
    string += ')'

    return string


def extract_funcdef(node):
    """Extract positional-only arguments from function parameters.

    Args:
     - node -- parso.python.tree.PythonNode, AST of function parameters

    Returns:
     - list[parso.python.tree.Param] -- extracted positional-only arguments

    """
    pos_only = list()

    pos_temp = list()
    for child in node.children[1:-1]:
        if child.type == 'param':
            pos_temp.append(child)
        elif child.type == 'operator' and child.value == '/':
            pos_only.extend(pos_temp)
            break

    return pos_only


def walk(node):
    """Walk parso AST.

    Args:
     - node -- typing.Union[parso.python.tree.Module,
                            parso.python.tree.PythonNode,
                            parso.python.tree.PythonLeaf], parso AST

    Envs:
     - POSUER_LINSEP -- line separator to process source files (same as `--linsep` option in CLI)
     - POSUER_DISMISS -- dismiss runtime checks for positional-only arguments (same as `--dismiss` option in CLI)
     - POSUER_LINTING -- lint converted codes (same as `--linting` option in CLI)

    Returns:
     - str -- converted string
     - bool -- if contains positional-only arguments

    """

    POSUER_DISMISS = BOOLEAN_STATES.get(os.getenv('POSUER_DISMISS', '0').casefold(), False)
    if isinstance(node, parso.python.tree.Module) and (not POSUER_DISMISS):
        prefix = ''
        suffix = ''

        indent = False
        poflag = False
        for child in node.children:
            if child.get_first_leaf().column != 0:
                indent = True
            walk_string, walk_flag = walk(child)
            if indent:
                suffix += walk_string
            else:
                prefix += walk_string
            if walk_flag:
                poflag = True

        if poflag:
            return (prefix + _decorator + suffix), poflag
        return (prefix + suffix), poflag

    string = ''
    poflag = False
    walk_flag = False

    if node.type == 'funcdef':
        funcdef = ''
        for child in node.children:
            if child.type == 'parameters':
                parameters = extract_funcdef(child)
                if parameters:
                    walk_flag = True
                    funcdef += dismiss_funcdef(child)
                else:
                    funcdef += child.get_code()
            elif child.type == 'suite':
                walk_string, walk_flag = walk(child)
                string += walk_string
            else:
                funcdef += node.get_code()
            if walk_flag:
                poflag = True
        if parameters and (not POSUER_DISMISS):
            column = node.get_first_leaf().column
            string += decorate_funcdef(parameters, column, funcdef)
        else:
            string += funcdef
        return string, poflag

    if node.type == 'lambdef':
        parameters = extract_lambdef(node)
        if parameters:
            walk_flag = True
            lambdef = dismiss_lambdef(node)
            if not POSUER_DISMISS:
                lambdef = decorate_lambdef(parameters, lambdef)
            string += lambdef
        else:
            string += node.get_code()
        if walk_flag:
            poflag = True
        return string

    if isinstance(node, parso.python.tree.PythonLeaf):
        string += node.get_code()

    if hasattr(node, 'children'):
        for child in node.children:
            walk_string, walk_flag = walk(child)
            string += walk_string

    if walk_flag:
        poflag = True
    return string, poflag


def convert(string, source='<unknown>'):
    """The main conversion process.

    Args:
     - string -- str, context to be converted
     - source -- str, source of the context

    Envs:
     - POSUER_VERSION -- convert against Python version (same as `--python` option in CLI)
     - POSUER_LINSEP -- line separator to process source files (same as `--linsep` option in CLI)
     - POSUER_DISMISS -- dismiss runtime checks for positional-only arguments (same as `--dismiss` option in CLI)
     - POSUER_LINTING -- lint converted codes (same as `--linting` option in CLI)

    Returns:
     - str -- converted string

    """
    # parse source string
    module = parse(string, source)

    # convert source string
    string, _ = walk(module)

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
     - POSUER_LINSEP -- line separator to process source files (same as `--linsep` option in CLI)
     - POSUER_DISMISS -- dismiss runtime checks for positional-only arguments (same as `--dismiss` option in CLI)
     - POSUER_LINTING -- lint converted codes (same as `--linting` option in CLI)

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
__posuer_linesep__ = os.getenv('POSUER_LINESEP', os.linesep)


def get_parser():
    """Generate CLI parser.

    Returns:
     - argparse.ArgumentParser -- CLI parser for posuer

    """
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
    convert_group.add_argument('-s', '--linsep', action='store', default=__posuer_linesep__, metavar='SEP',
                               help='line separator to process source files (%s)' % __posuer_linesep__)
    convert_group.add_argument('-d', '--dismiss', action='store_true',
                               help='dismiss runtime checks for positional-only parameters')
    convert_group.add_argument('-l', '--linting', action='store_true',
                               help='lint converted codes')

    parser.add_argument('file', nargs='+', metavar='SOURCE', default=__cwd__,
                        help='python source files and folders to be converted (%s)' % __cwd__)

    return parser


def main(argv=None):
    """Entry point for posuer.

    Args:
     - argv -- list[str], CLI arguments (default: None)

    Envs:
     - POSUER_QUIET -- run in quiet mode (same as `--quiet` option in CLI)
     - POSUER_ENCODING -- encoding to open source files (same as `--encoding` option in CLI)
     - POSUER_VERSION -- convert against Python version (same as `--python` option in CLI)
     - POSUER_LINSEP -- line separator to process source files (same as `--linsep` option in CLI)
     - POSUER_DISMISS -- dismiss runtime checks for positional-only arguments (same as `--dismiss` option in CLI)
     - POSUER_LINTING -- lint converted codes (same as `--linting` option in CLI)

    """
    parser = get_parser()
    args = parser.parse_args(argv)

    # set up variables
    ARCHIVE = args.archive_path
    archive = (not args.no_archive)
    os.environ['POSUER_VERSION'] = args.python
    os.environ['POSUER_ENCODING'] = args.encoding
    os.environ['POSUER_LINSEP'] = args.linsep
    POSUER_QUIET = os.getenv('POSUER_QUIET')
    os.environ['POSUER_QUIET'] = '1' if args.quiet else ('0' if POSUER_QUIET is None else POSUER_QUIET)
    POSUER_DISMISS = os.getenv('POSUER_DISMISS')
    os.environ['POSUER_DISMISS'] = '1' if args.dismiss else ('0' if POSUER_DISMISS is None else POSUER_DISMISS)
    POSUER_LINTING = os.getenv('POSUER_LINTING')
    os.environ['POSUER_LINTING'] = '1' if args.dismiss else ('0' if POSUER_LINTING is None else POSUER_LINTING)

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
