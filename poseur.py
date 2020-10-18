# -*- coding: utf-8 -*-
"""Back-port compiler for Python 3.8 positional-only parameter syntax."""

import argparse
import os
import pathlib
import re
import sys
import traceback

import f2format
import tbtrim
from bpc_utils import (BaseContext, BPCSyntaxError, Config, TaskLock, archive_files,
                       detect_encoding, detect_files, detect_indentation, detect_linesep,
                       first_non_none, get_parso_grammar_versions, map_tasks, parse_boolean_state,
                       parse_indentation, parse_linesep, parse_positive_integer, parso_parse,
                       recover_files)

__all__ = ['main', 'poseur', 'convert', 'decorator']  # pylint: disable=undefined-all-variable

# version string
__version__ = '0.4.3'

##############################################################################
# Auxiliaries

#: Get supported source versions.
#:
#: .. seealso:: :func:`bpc_utils.get_parso_grammar_versions`
POSEUR_SOURCE_VERSIONS = get_parso_grammar_versions(minimum='3.8')

# option default values
#: Default value for the ``quiet`` option.
_default_quiet = False
#: Default value for the ``concurrency`` option.
_default_concurrency = None  # auto detect
#: Default value for the ``do_archive`` option.
_default_do_archive = True
#: Default value for the ``archive_path`` option.
_default_archive_path = 'archive'
#: Default value for the ``source_version`` option.
_default_source_version = POSEUR_SOURCE_VERSIONS[-1]
#: Default value for the ``linesep`` option.
_default_linesep = None  # auto detect
#: Default value for the ``indentation`` option.
_default_indentation = None  # auto detect
#: Default value for the ``pep8`` option.
_default_pep8 = True

# option getter utility functions
# option value precedence is: explicit value (CLI/API arguments) > environment variable > default value


def _get_quiet_option(explicit=None):
    """Get the value for the ``quiet`` option.

    Args:
        explicit (Optional[bool]): the value explicitly specified by user,
            :data:`None` if not specified

    Returns:
        bool: the value for the ``quiet`` option

    :Environment Variables:
        :envvar:`POSEUR_QUIET` -- the value in environment variable

    See Also:
        :data:`_default_quiet`

    """
    # We need lazy evaluation, so first_non_none(a, b, c) does not work here
    # with PEP 505 we can simply write a ?? b ?? c
    def _option_layers():
        yield explicit
        yield parse_boolean_state(os.getenv('POSEUR_QUIET'))
        yield _default_quiet
    return first_non_none(_option_layers())


def _get_concurrency_option(explicit=None):
    """Get the value for the ``concurrency`` option.

    Args:
        explicit (Optional[int]): the value explicitly specified by user,
            :data:`None` if not specified

    Returns:
        Optional[int]: the value for the ``concurrency`` option;
        :data:`None` means *auto detection* at runtime

    :Environment Variables:
        :envvar:`POSEUR_CONCURRENCY` -- the value in environment variable

    See Also:
        :data:`_default_concurrency`

    """
    return parse_positive_integer(explicit or os.getenv('POSEUR_CONCURRENCY') or _default_concurrency)


def _get_do_archive_option(explicit=None):
    """Get the value for the ``do_archive`` option.

    Args:
        explicit (Optional[bool]): the value explicitly specified by user,
            :data:`None` if not specified

    Returns:
        bool: the value for the ``do_archive`` option

    :Environment Variables:
        :envvar:`POSEUR_DO_ARCHIVE` -- the value in environment variable

    See Also:
        :data:`_default_do_archive`

    """
    def _option_layers():
        yield explicit
        yield parse_boolean_state(os.getenv('POSEUR_DO_ARCHIVE'))
        yield _default_do_archive
    return first_non_none(_option_layers())


def _get_archive_path_option(explicit=None):
    """Get the value for the ``archive_path`` option.

    Args:
        explicit (Optional[str]): the value explicitly specified by user,
            :data:`None` if not specified

    Returns:
        str: the value for the ``archive_path`` option

    :Environment Variables:
        :envvar:`POSEUR_ARCHIVE_PATH` -- the value in environment variable

    See Also:
        :data:`_default_archive_path`

    """
    return explicit or os.getenv('POSEUR_ARCHIVE_PATH') or _default_archive_path


def _get_source_version_option(explicit=None):
    """Get the value for the ``source_version`` option.

    Args:
        explicit (Optional[str]): the value explicitly specified by user,
            :data:`None` if not specified

    Returns:
        str: the value for the ``source_version`` option

    :Environment Variables:
        :envvar:`POSEUR_SOURCE_VERSION` -- the value in environment variable

    See Also:
        :data:`_default_source_version`

    """
    return explicit or os.getenv('POSEUR_SOURCE_VERSION') or _default_source_version


def _get_linesep_option(explicit=None):
    r"""Get the value for the ``linesep`` option.

    Args:
        explicit (Optional[str]): the value explicitly specified by user,
            :data:`None` if not specified

    Returns:
        Optional[Literal['\\n', '\\r\\n', '\\r']]: the value for the ``linesep`` option;
        :data:`None` means *auto detection* at runtime

    :Environment Variables:
        :envvar:`POSEUR_LINESEP` -- the value in environment variable

    See Also:
        :data:`_default_linesep`

    """
    return parse_linesep(explicit or os.getenv('POSEUR_LINESEP') or _default_linesep)


def _get_indentation_option(explicit=None):
    """Get the value for the ``indentation`` option.

    Args:
        explicit (Optional[Union[str, int]]): the value explicitly specified by user,
            :data:`None` if not specified

    Returns:
        Optional[str]: the value for the ``indentation`` option;
        :data:`None` means *auto detection* at runtime

    :Environment Variables:
        :envvar:`POSEUR_INDENTATION` -- the value in environment variable

    See Also:
        :data:`_default_indentation`

    """
    return parse_indentation(explicit or os.getenv('POSEUR_INDENTATION') or _default_indentation)


def _get_pep8_option(explicit=None):
    """Get the value for the ``pep8`` option.

    Args:
        explicit (Optional[bool]): the value explicitly specified by user,
            :data:`None` if not specified

    Returns:
        bool: the value for the ``pep8`` option

    :Environment Variables:
        :envvar:`POSEUR_PEP8` -- the value in environment variable

    See Also:
        :data:`_default_pep8`

    """
    def _option_layers():
        yield explicit
        yield parse_boolean_state(os.getenv('POSEUR_PEP8'))
        yield _default_pep8
    return first_non_none(_option_layers())


###############################################################################
# Traceback Trimming (tbtrim)

# root path
ROOT = pathlib.Path(__file__).resolve().parent


def predicate(filename):
    return pathlib.Path(filename).parent == ROOT


tbtrim.set_trim_rule(predicate, strict=True, target=BPCSyntaxError)

###############################################################################
# Positional-only decorator

# cf. https://mail.python.org/pipermail/python-ideas/2017-February/044888.html
DECORATOR_TEMPLATE = '''\
def %(decorator)s(*poseur):
%(indentation)s"""Positional-only parameters runtime checker.
%(indentation)s
%(indentation)s    Args:
%(indentation)s        *poseur: Name list of positional-only parameters.
%(indentation)s
%(indentation)s    Raises:
%(indentation)s        TypeError: If any position-only parameters were passed as
%(indentation)s            keyword parameters.
%(indentation)s
%(indentation)s    The decorator function may decorate regular :term:`function` and/or
%(indentation)s    :term:`lambda` function to provide runtime checks on the original
%(indentation)s    positional-only parameters.
%(indentation)s
%(indentation)s"""
%(indentation)simport functools
%(indentation)sdef caller(func):
%(indentation)s%(indentation)s@functools.wraps(func)
%(indentation)s%(indentation)sdef wrapper(*args, **kwargs):
%(indentation)s%(indentation)s%(indentation)sposeur_args = set(poseur).intersection(kwargs)
%(indentation)s%(indentation)s%(indentation)sif poseur_args:
%(indentation)s%(indentation)s%(indentation)s%(indentation)sraise TypeError('%%s() got some positional-only parameters passed as keyword arguments: %%r' %% (func.__name__, ', '.join(poseur_args)))
%(indentation)s%(indentation)s%(indentation)sreturn func(*args, **kwargs)
%(indentation)s%(indentation)sreturn wrapper
%(indentation)sreturn caller
'''.splitlines()  # `str.splitlines` will remove trailing newline

exec(os.linesep.join(DECORATOR_TEMPLATE) % dict(decorator='decorator', indentation='    '))  # nosec: B102; pylint: disable=exec-used

###############################################################################
# Main convertion implementation


class Context(BaseContext):
    """General conversion context.

    Args:
        node (parso.tree.NodeOrLeaf): parso AST
        config (Config): conversion configurations

    Keyword Args:
        indent_level (int): current indentation level
        raw (bool): raw processing flag

    Important:
        ``raw`` should be :data:`True` only if the ``node`` is in the clause of another *context*,
        where the converted wrapper functions should be inserted.

    For the :class:`Context` class of :mod:`poseur` module,
    it will process nodes with following methods:

    * :token:`suite`

      - :meth:`Context._process_suite_node`

    * :token:`funcdef`

      - :meth:`Context._process_funcdef`

    * :token:`lambdef`

      - :meth:`Context._process_lambdef`

    * :token:`async_funcdef`

      - :meth:`Context._process_async_funcdef`

    * :token:`async_stmt`

      - :meth:`Context._process_async_stmt`

    * :token:`classdef`

      - :meth:`Context._process_classdef`

    * :token:`if_stmt`

      - :meth:`Context._process_if_stmt`

    * :token:`while_stmt`

      - :meth:`Context._process_while_stmt`

    * :token:`for_stmt`

      - :meth:`Context._process_for_stmt`

    * :token:`with_stmt`

      - :meth:`Context._process_with_stmt`

    * :token:`try_stmt`

      - :meth:`Context._process_try_stmt`

    * :token:`stringliteral`

      * :meth:`Context._process_strings`
      * :meth:`Context._process_string_context`

    * :token:`f_string`

      * :meth:`Context._process_fstring`

    """
    #: re.Pattern: Pattern to find the function definition line.
    pattern_funcdef = re.compile(r'^\s*(async\s+)?def\s', re.ASCII)

    @property
    def decorator(self):
        """Name of the ``poseur`` decorator.

        :rtype: str
        """
        return self._decorator

    def __init__(self, node, config, *, indent_level=0, raw=False):
        #: bool: Dismiss runtime checks for positional-only parameters.
        self._dismiss = config.dismiss
        #: str: Decorator name.
        self._decorator = config.decorator

        super().__init__(node, config, indent_level=indent_level, raw=raw)

    def _process_funcdef(self, node, *, async_ctx=None):
        """Process function definition (:token:`funcdef`).

        Args:
            node (parso.python.tree.Function): function node

        Keyword Args:
            async_ctx (parso.python.tree.Keyword): ``async`` keyword AST node

        """
        if not self.has_expr(node):
            self += node.get_code()
            return

        posonly = list()  # positional-only parameters
        funcdef = '' if async_ctx is None else async_ctx.get_code()

        # 'def' NAME '(' PARAM ')' [ '->' NAME ] ':' SUITE
        for child in node.children[:-1]:
            if child.type == 'parameters':
                # <Operator: (>
                funcdef += child.children[0].get_code()

                parameters = ''
                param_list = list()
                for grandchild in child.children[1:-1]:
                    # <Operator: />
                    if grandchild.type == 'operator' and grandchild.value == '/':
                        parameters += grandchild.get_code().replace('/', '')
                        posonly.extend(param_list)
                        continue

                    # <Param: ...>
                    if grandchild.type == 'param':
                        param_list.append(grandchild)

                        if grandchild.default is not None:
                            # initiate new context
                            ctx = Context(grandchild, self.config, raw=True,
                                          indent_level=self._indent_level)
                            parameters += ctx.string
                            continue

                    # <Param: ...> / <Operator: *> / <Operator: ,>
                    parameters += grandchild.get_code()

                if self._pep8:
                    funcdef += ', '.join(filter(None, map(lambda s: s.strip(), parameters.split(','))))
                else:
                    funcdef += ','.join(filter(lambda s: s.strip(), parameters.split(',')))

                # <Operator: )>
                funcdef += child.children[-1].get_code()
                continue

            funcdef += child.get_code()

        # decorate the function
        if not self._dismiss and posonly:
            prefix = ''
            suffix = ''
            deflag = False  # function definition line

            for line in funcdef.splitlines(True):
                if self.pattern_funcdef.match(line) is not None:
                    deflag = True
                if deflag:
                    suffix += line
                else:
                    prefix += line

            posonly_args = ', '.join(map(lambda param: repr(param.name.value), posonly))
            indentation = self._indentation * self._indent_level
            self += ('%(prefix)s'
                     '%(indentation)s@%(decorator)s(%(posonly)s)%(linesep)s'
                     '%(suffix)s') % dict(
                         prefix=prefix, suffix=suffix,
                         linesep=self._linesep, indentation=indentation,
                         decorator=self._decorator, posonly=posonly_args,
                     )
        else:
            self += funcdef

        # SUITE
        self._process_suite_node(node.children[-1])

    def _process_async_stmt(self, node):
        """Process ``async`` statement (:token:`async_stmt`).

        Args:
            node (parso.python.tree.PythonNode): ``async`` statement node

        This method processes an ``async`` statement node. If such statement is an
        *async* :term:`function`, then it will pass on the processing to
        :meth:`self._process_funcdef <Context._process_funcdef>`.

        """
        child_1st = node.children[0]
        child_2nd = node.children[1]

        flag_1st = child_1st.type == 'keyword' and child_1st.value == 'async'
        flag_2nd = child_2nd.type == 'funcdef'

        if flag_1st and flag_2nd:
            self._process_funcdef(child_2nd, async_ctx=child_1st)
            return

        self._process(child_1st)
        self._process(child_2nd)

    def _process_async_funcdef(self, node):
        """Process ``async`` function definition (:token:`async_funcdef`).

        Args:
            node (parso.python.tree.PythonNode): ``async`` function node

        This method processes an ``async`` function node. It will extract
        the ``async`` keyword node (:class:`parso.python.tree.Keyword`)
        and the :term:`function` node (:class:`parso.python.tree.Function`)
        then pass on the processing to
        :meth:`self._process_funcdef <Context._process_funcdef>`.

        """
        async_ctx, funcdef = node.children
        self._process_funcdef(funcdef, async_ctx=async_ctx)

    def _process_lambdef(self, node):
        """Process lambda definition (:token:`lambdef`).

        Args:
            node (parso.python.tree.Lambda): lambda node

        """
        if not self.has_expr(node):
            self += node.get_code()
            return

        pos_only = list()
        children = iter(node.children)

        # string buffers
        params = ''
        prefix = ''
        suffix = ''

        # <Keyword: lambda>
        prefix += next(children).get_code()

        # vararglist
        param_list = list()
        for child in children:
            if child.type == 'operator':
                # <Operator: />
                if child.value == '/':
                    params += child.get_code().replace('/', '')
                    pos_only.extend(param_list)
                    continue

                # <Operator: :>
                if child.value == ':':
                    suffix += child.get_code()
                    break

            # <Param: ...>
            if child.type == 'param':
                param_list.append(child)

                if child.default is not None:
                    # initialize new context
                    ctx = Context(node=child, config=self.config,
                                  indent_level=self._indent_level, raw=True)
                    params += ctx.string
                    continue

            # <Param: ...> / <Operator: *> / <Operator: ,>
            params += child.get_code()

        # test_nocond | test
        ctx = Context(node=next(children), config=self.config,
                      indent_level=self._indent_level, raw=True)
        suffix += ctx.string

        whitespace_prefix, whitespace_suffix = self.extract_whitespaces(params)
        if self._pep8:
            params = ', '.join(filter(None, map(lambda s: s.strip(), params.split(','))))
        else:
            params = ','.join(filter(lambda s: s.strip(), params.split(',')))
        lambdef = prefix + whitespace_prefix + params.strip() + whitespace_suffix + suffix

        if self._dismiss or not pos_only:
            self += lambdef
            return

        # decorate lambda definition
        whitespace_prefix, whitespace_suffix = self.extract_whitespaces(lambdef)
        posonly_args = ', '.join(map(lambda param: repr(param.name.value), pos_only))
        self += ('%(prefix)s'
                 '%(decorator)s(%(posonly)s)'
                 '(%(lambdef)s)'
                 '%(suffix)s') % dict(
                     prefix=whitespace_prefix, suffix=whitespace_suffix,
                     lambdef=lambdef.strip(),
                     decorator=self._decorator, posonly=posonly_args,
                 )

    def _process_suite_node(self, node):
        """Process indented suite (:token:`suite` or others).

        Args:
            node (parso.tree.NodeOrLeaf): suite node

        This method first checks if ``node`` contains positional-only parameters.
        If not, it will not perform any processing, rather just append the
        original source code to context buffer.

        If ``node`` contains positional-only parameters, then it will initiate
        another Context` instance to perform the conversion process on such
        ``node``.

        """
        if not self.has_expr(node):
            self += node.get_code()
            return

        indent = self._indent_level + 1
        self += self._linesep + self._indentation * indent

        # initialize new context
        ctx = Context(node=node, config=self.config,
                      indent_level=indent, raw=True)
        self += ctx.string.lstrip()

    def _process_string_context(self, node):
        """Process string contexts (:token:`stringliteral`).

        Args:
            node (parso.python.tree.PythonNode): string literals node

        This method first checks if ``node`` contains position-only parameters.
        If not, it will not perform any processing, rather just append the
        original source code to context buffer. Later it will check if
        ``node`` contains *debug f-string*. If not, it will process the
        *regular* processing on each child of such ``node``.

        See Also:
            The method calls :meth:`f2format.Context.has_debug_fstring`
            to detect *debug f-strings*.

        Otherwise, it will initiate a new :class:`StringContext` instance
        to perform the conversion process on such ``node``, which will first
        use :mod:`f2format` to convert those formatted string literals.

        Important:
            When initialisation, ``raw`` parameter **must** be set to :data:`True`;
            as the converted wrapper functions should be inserted in the *outer*
            context, rather than the new :class:`StringContext` instance.

        """
        if not self.has_expr(node):
            self += node.get_code()
            return

        # TODO: reconstruct f2format and implement such method for the case
        # if not f2format.Context.has_debug_fstring(node):
        if True:  # pylint: disable=using-constant-test
            for child in node.children:
                self._process(child)
            return

        # initiate new context
        ctx = StringContext(node=node, config=self.config,
                            indent_level=self._indent_level, raw=True)
        self += ctx.string

    def _process_classdef(self, node):
        """Process class definition (:token:`classdef`).

        Args:
            node (parso.python.tree.Class): class node

        This method converts the whole class suite context with
        :meth:`~Context._process_suite_node` through :class:`Context`
        respectively.

        """
        # <Keyword: class>
        # <Name: ...>
        # [<Operator: (>, PythonNode(arglist, [...]]), <Operator: )>]
        # <Operator: :>
        for child in node.children[:-1]:
            self._process(child)

        # PythonNode(suite, [...]) / PythonNode(simple_stmt, [...])
        suite = node.children[-1]
        self._process_suite_node(suite)

    def _process_if_stmt(self, node):
        """Process if statement (:token:`if_stmt`).

        Args:
            node (parso.python.tree.IfStmt): if node

        This method processes each indented suite under the *if*, *elif*,
        and *else* statements.

        """
        children = iter(node.children)

        # <Keyword: if>
        self._process(next(children))
        # namedexpr_test
        self._process(next(children))
        # <Operator: :>
        self._process(next(children))
        # suite
        self._process_suite_node(next(children))

        while True:
            try:
                # <Keyword: elif | else>
                key = next(children)
            except StopIteration:
                break
            self._process(key)

            if key.value == 'elif':
                # namedexpr_test
                self._process(next(children))
                # <Operator: :>
                self._process(next(children))
                # suite
                self._process_suite_node(next(children))
                continue
            if key.value == 'else':
                # <Operator: :>
                self._process(next(children))
                # suite
                self._process_suite_node(next(children))
                continue

    def _process_while_stmt(self, node):
        """Process while statement (:token:`while_stmt`).

        Args:
            node (parso.python.tree.WhileStmt): while node

        This method processes the indented suite under the *while* and optional
        *else* statements.

        """
        children = iter(node.children)

        # <Keyword: while>
        self._process(next(children))
        # namedexpr_test
        self._process(next(children))
        # <Operator: :>
        self._process(next(children))
        # suite
        self._process_suite_node(next(children))

        try:
            key = next(children)
        except StopIteration:
            return

        # <Keyword: else>
        self._process(key)
        # <Operator: :>
        self._process(next(children))
        # suite
        self._process_suite_node(next(children))

    def _process_for_stmt(self, node):
        """Process for statement (:token:`for_stmt`).

        Args:
            node (parso.python.tree.ForStmt): for node

        This method processes the indented suite under the *for* and optional
        *else* statements.

        """
        children = iter(node.children)

        # <Keyword: for>
        self._process(next(children))
        # exprlist
        self._process(next(children))
        # <Keyword: in>
        self._process(next(children))
        # testlist
        self._process(next(children))
        # <Operator: :>
        self._process(next(children))
        # suite
        self._process_suite_node(next(children))

        try:
            key = next(children)
        except StopIteration:
            return

        # <Keyword: else>
        self._process(key)
        # <Operator: :>
        self._process(next(children))
        # suite
        self._process_suite_node(next(children))

    def _process_with_stmt(self, node):
        """Process with statement (:token:`with_stmt`).

        Args:
            node (parso.python.tree.WithStmt): with node

        This method processes the indented suite under the *with* statement.

        """
        children = iter(node.children)

        # <Keyword: with>
        self._process(next(children))

        while True:
            # with_item | <Operator: ,>
            item = next(children)
            self._process(item)

            # <Operator: :>
            if item.type == 'operator' and item.value == ':':
                break

        # suite
        self._process_suite_node(next(children))

    def _process_try_stmt(self, node):
        """Process try statement (:token:`try_stmt`).

        Args:
            node (parso.python.tree.TryStmt): try node

        This method processes the indented suite under the *try*, *except*,
        *else*, and *finally* statements.

        """
        children = iter(node.children)

        while True:
            try:
                key = next(children)
            except StopIteration:
                break

            # <Keyword: try | else | finally> | PythonNode(except_clause, [...]
            self._process(key)
            # <Operator: :>
            self._process(next(children))
            # suite
            self._process_suite_node(next(children))

    def _process_strings(self, node):
        """Process concatenable strings (:token:`stringliteral`).

        Args:
            node (parso.python.tree.PythonNode): concatentable strings node

        As in Python, adjacent string literals can be concatenated in certain
        cases, as described in the `documentation`_. Such concatenable strings
        may contain formatted string literals (:term:`f-string`) within its scope.

        _documentation: https://docs.python.org/3/reference/lexical_analysis.html#string-literal-concatenation

        """
        self._process_string_context(node)

    def _process_fstring(self, node):
        """Process formatted strings (:token:`f_string`).

        Args:
            node (parso.python.tree.PythonNode): formatted strings node

        """
        self._process_string_context(node)

    def _concat(self):
        """Concatenate final string.

        This method tries to inserted the runtime check decorator function
        at the very location where starts to contain positional-only parameters, i.e.
        between the converted code as :attr:`self._prefix <Context._prefix>` and
        :attr:`self._suffix <Context._suffix>`.

        The inserted code is rendered from :data:`DECORATOR_TEMPLATE`. If
        :attr:`self._pep8 <Context._pep8>` is :data:`True`, it will insert the code
        in compliance with :pep:`8`.

        """
        if self._dismiss:
            self._buffer += self._prefix + self._suffix
            return

        # strip suffix comments
        prefix, suffix = self.split_comments(self._suffix, self._linesep)
        suffix_linesep = re.match(rf'^(?P<linesep>({self._linesep})*)', suffix, flags=re.ASCII).group('linesep')

        # first, the prefix code
        self._buffer += self._prefix + prefix + suffix_linesep
        if self._pep8 and self._buffer:
            if (self._node_before_expr is not None
                    and self._node_before_expr.type in ('funcdef', 'classdef')
                    and self._indent_level == 0):
                blank = 2
            else:
                blank = 1
            self._buffer += self._linesep * self.missing_newlines(prefix=self._buffer, suffix='',
                                                                  expected=blank, linesep=self._linesep)

        # then, the decorator function
        self._buffer += self._linesep.join(DECORATOR_TEMPLATE) % dict(
            decorator=self._decorator,
            indentation=self._indentation,
        ) + self._linesep

        # finally, the suffix code
        if self._pep8:
            self._buffer += self._linesep * self.missing_newlines(prefix=self._buffer, suffix='',
                                                                  expected=2, linesep=self._linesep)
        self._buffer += suffix.lstrip(self._linesep)

    @classmethod
    def has_expr(cls, node):
        """Check if node has positional-only parameters.

        Args:
            node (parso.tree.NodeOrLeaf): parso AST

        Returns:
            bool: if ``node`` has positional-only parameters

        """
        if node.type == 'funcdef':
            return cls._check_funcdef(node)
        if node.type == 'lambdef':
            return cls._check_lambdef(node)
        if not hasattr(node, 'children'):
            return False
        return any(map(cls.has_expr, node.children))

    # backward compatibility and auxiliary alias
    has_poseur = has_expr

    @classmethod
    def _check_funcdef(cls, node):
        """Check if :term:`function` definition contains positional-only parameters.

        Args:
            node (parso.tree.Function): function definition

        Returns:
            bool: if :term:`function` definition contains positional-only parameters

        """
        for child in node.children:
            if child.type == 'parameters':
                for param in child.children[1:-1]:
                    if param.type == 'operator':
                        if param.value == '/':
                            return True
                        continue
                    if param.default is not None and cls.has_expr(param.default):
                        return True
            elif cls.has_expr(child):  # suite / ...
                return True
        return False

    @classmethod
    def _check_lambdef(cls, node):
        """Check if :term:`lambda` definition contains positional-only parameters.

        Args:
            node (parso.tree.Lambda): lambda definition

        Returns:
            bool: if :term:`lambda` definition contains positional-only parameters

        """
        param = False
        suite = False
        for child in node.children:
            if child.type == 'param':
                if child.default is not None:
                    if cls.has_expr(child.default):
                        return True
                param = True
            elif child.type == 'operator' and child.value == ':':
                param = False
                suite = True
            elif param and child.type == 'operator' and child.value == '/':
                return True
            elif suite and cls.has_expr(child):
                return True
        return False


class StringContext(Context):
    """String (f-string) conversion context.

    This class is mainly used for converting **formatted strings**.

    Args:
        node (parso.python.tree.PythonNode): parso AST
        config (Config): conversion configurations

    Keyword Args:
        indent_level (int): current indentation level
        raw (Literal[True]): raw processing flag

    Note:
        * ``raw`` should always be :data:`True`.

    As the conversion in :class:`Context` changes the original expression,
    which may change the content of *debug f-string*.

    """

    def __init__(self, node, config, *, indent_level=0, raw=False):
        # convert using f2format first
        prefix, suffix = self.extract_whitespaces(node.get_code())
        code = f2format.convert(node.get_code().strip())
        node = parso_parse(code, filename=config.filename, version=config.source_version)

        # call super init
        super().__init__(node=node, config=config,
                         indent_level=indent_level, raw=raw)
        self._buffer = prefix + self._buffer + suffix


# TODO: add misc functions required for ``dismiss`` and ``decorator`` (or equivalence)
def convert(code, filename=None, *, source_version=None, linesep=None,
            indentation=None, pep8=None, dismiss=None, decorator=None):
    """Convert the given Python source code string.

    Args:
        code (Union[str, bytes]): the source code to be converted
        filename (Optional[str]): an optional source file name to provide a context in case of error

    Keyword Args:
        source_version (Optional[str]): parse the code as this Python version (uses the latest version by default)
        linesep (Optional[str]): line separator of code (``LF``, ``CRLF``, ``CR``) (auto detect by default)
        indentation (Optional[Union[int, str]]): code indentation style, specify an integer for the number of spaces,
            or ``'t'``/``'tab'`` for tabs (auto detect by default)
        pep8 (Optional[bool]): whether to make code insertion :pep:`8` compliant

    :Environment Variables:
     - :envvar:`POSEUR_SOURCE_VERSION` -- same as the ``source_version`` argument and the ``--source-version`` option
        in CLI
     - :envvar:`POSEUR_LINESEP` -- same as the `linesep` `argument` and the ``--linesep`` option in CLI
     - :envvar:`POSEUR_INDENTATION` -- same as the ``indentation`` argument and the ``--indentation`` option in CLI
     - :envvar:`POSEUR_PEP8` -- same as the ``pep8`` argument and the ``--no-pep8`` option in CLI (logical negation)

    Returns:
        str: converted source code

    """
    # parse source string
    source_version = _get_source_version_option(source_version)
    module = parso_parse(code, filename=filename, version=source_version)

    # get linesep, indentation and pep8 options
    linesep = _get_linesep_option(linesep)
    indentation = _get_indentation_option(indentation)
    if linesep is None:
        linesep = detect_linesep(code)
    if indentation is None:
        indentation = detect_indentation(code)
    pep8 = _get_pep8_option(pep8)

    # pack conversion configuration
    config = Config(linesep=linesep, indentation=indentation, pep8=pep8,
                    filename=filename, source_version=source_version,
                    dismiss=dismiss, decorator=decorator)

    # convert source string
    result = Context(module, config).string

    # return conversion result
    return result


# TODO: add misc functions required for ``dismiss`` and ``decorator`` (or equivalence)
def poseur(filename, *, source_version=None, linesep=None, indentation=None, pep8=None,
           dismiss=None, decorator=None, quiet=None, dry_run=False):
    """Convert the given Python source code file. The file will be overwritten.

    Args:
        filename (str): the file to convert

    Keyword Args:
        source_version (Optional[str]): parse the code as this Python version (uses the latest version by default)
        linesep (Optional[str]): line separator of code (``LF``, ``CRLF``, ``CR``) (auto detect by default)
        indentation (Optional[Union[int, str]]): code indentation style, specify an integer for the number of spaces,
            or ``'t'``/``'tab'`` for tabs (auto detect by default)
        pep8 (Optional[bool]): whether to make code insertion :pep:`8` compliant
        quiet (Optional[bool]): whether to run in quiet mode
        dry_run (bool): if :data:`True`, only print the name of the file to convert but do not perform any conversion

    :Environment Variables:
     - :envvar:`POSEUR_SOURCE_VERSION` -- same as the ``source-version`` argument and the ``--source-version`` option
        in CLI
     - :envvar:`POSEUR_LINESEP` -- same as the ``linesep`` argument and the ``--linesep`` option in CLI
     - :envvar:`POSEUR_INDENTATION` -- same as the ``indentation`` argument and the ``--indentation`` option in CLI
     - :envvar:`POSEUR_PEP8` -- same as the ``pep8`` argument and the ``--no-pep8`` option in CLI (logical negation)
     - :envvar:`POSEUR_QUIET` -- same as the ``quiet`` argument and the ``--quiet`` option in CLI

    """
    quiet = _get_quiet_option(quiet)
    if not quiet:
        with TaskLock():
            print('Now converting: %r' % filename, file=sys.stderr)
    if dry_run:
        return

    # read file content
    with open(filename, 'rb') as file:
        content = file.read()

    # detect source code encoding
    encoding = detect_encoding(content)

    # get linesep and indentation
    linesep = _get_linesep_option(linesep)
    indentation = _get_indentation_option(indentation)
    if linesep is None or indentation is None:
        with open(filename, 'r', encoding=encoding) as file:
            if linesep is None:
                linesep = detect_linesep(file)
            if indentation is None:
                indentation = detect_indentation(file)

    # do the dirty things
    result = convert(content, filename=filename, source_version=source_version,
                     linesep=linesep, indentation=indentation, pep8=pep8)

    # overwrite the file with conversion result
    with open(filename, 'w', encoding=encoding, newline='') as file:
        file.write(result)


###############################################################################
# CLI & Entry Point

# option values display
# these values are only intended for argparse help messages
# this shows default values by default, environment variables may override them
__cwd__ = os.getcwd()
__poseur_quiet__ = 'quiet mode' if _get_quiet_option() else 'non-quiet mode'
__poseur_concurrency__ = _get_concurrency_option() or 'auto detect'
__poseur_do_archive__ = 'will do archive' if _get_do_archive_option() else 'will not do archive'
__poseur_archive_path__ = os.path.join(__cwd__, _get_archive_path_option())
__poseur_source_version__ = _get_source_version_option()
__poseur_linesep__ = {
    '\n': 'LF',
    '\r\n': 'CRLF',
    '\r': 'CR',
    None: 'auto detect'
}[_get_linesep_option()]
__poseur_indentation__ = _get_indentation_option()
if __poseur_indentation__ is None:
    __poseur_indentation__ = 'auto detect'
elif __poseur_indentation__ == '\t':
    __poseur_indentation__ = 'tab'
else:
    __poseur_indentation__ = '%d spaces' % len(__poseur_indentation__)
__poseur_pep8__ = 'will conform to PEP 8' if _get_pep8_option() else 'will not conform to PEP 8'


def get_parser():
    """Generate CLI parser.

    Returns:
        argparse.ArgumentParser: CLI parser for poseur

    """
    parser = argparse.ArgumentParser(prog='poseur',
                                     usage='poseur [options] <Python source files and directories...>',
                                     description='Back-port compiler for Python 3.8 position-only parameters.')
    parser.add_argument('-V', '--version', action='version', version=__version__)
    parser.add_argument('-q', '--quiet', action='store_true', default=None,
                        help='run in quiet mode (current: %s)' % __poseur_quiet__)
    parser.add_argument('-C', '--concurrency', action='store', type=int, metavar='N',
                        help='the number of concurrent processes for conversion (current: %s)' % __poseur_concurrency__)
    parser.add_argument('--dry-run', action='store_true',
                        help='list the files to be converted without actually performing conversion and archiving')
    parser.add_argument('-s', '--simple', action='store', nargs='?', dest='simple_args', const='', metavar='FILE',
                        help='this option tells the program to operate in "simple mode"; '
                             'if a file name is provided, the program will convert the file but print conversion '
                             'result to standard output instead of overwriting the file; '
                             'if no file names are provided, read code for conversion from standard input and print '
                             'conversion result to standard output; '
                             'in "simple mode", no file names shall be provided via positional arguments')

    archive_group = parser.add_argument_group(title='archive options',
                                              description="backup original files in case there're any issues")
    archive_group.add_argument('-na', '--no-archive', action='store_false', dest='do_archive', default=None,
                               help='do not archive original files (current: %s)' % __poseur_do_archive__)
    archive_group.add_argument('-k', '--archive-path', action='store', default=__poseur_archive_path__, metavar='PATH',
                               help='path to archive original files (current: %(default)s)')
    archive_group.add_argument('-r', '--recover', action='store', dest='recover_file', metavar='ARCHIVE_FILE',
                               help='recover files from a given archive file')
    archive_group.add_argument('-r2', action='store_true', help='remove the archive file after recovery')
    archive_group.add_argument('-r3', action='store_true', help='remove the archive file after recovery, '
                                                                'and remove the archive directory if it becomes empty')

    # TODO: put back ``--dismiss`` & ``--decorator`` option (or equivalent)
    convert_group = parser.add_argument_group(title='convert options', description='conversion configuration')
    convert_group.add_argument('-vs', '-vf', '--source-version', '--from-version', action='store', metavar='VERSION',
                               default=__poseur_source_version__, choices=POSEUR_SOURCE_VERSIONS,
                               help='parse source code as this Python version (current: %(default)s)')
    convert_group.add_argument('-l', '--linesep', action='store',
                               help='line separator (LF, CRLF, CR) to read '
                                    'source files (current: %s)' % __poseur_linesep__)
    convert_group.add_argument('-t', '--indentation', action='store', metavar='INDENT',
                               help='code indentation style, specify an integer for the number of spaces, '
                                    "or 't'/'tab' for tabs (current: %s)" % __poseur_indentation__)
    convert_group.add_argument('-n8', '--no-pep8', action='store_false', dest='pep8', default=None,
                               help='do not make code insertion PEP 8 compliant (current: %s)' % __poseur_pep8__)

    parser.add_argument('files', action='store', nargs='*', metavar='<Python source files and directories...>',
                        help='Python source files and directories to be converted')

    return parser


def do_poseur(filename, **kwargs):
    """Wrapper function to catch exceptions."""
    try:
        poseur(filename, **kwargs)
    except Exception:  # pylint: disable=broad-except
        with TaskLock():
            print('Failed to convert file: %r' % filename, file=sys.stderr)
            traceback.print_exc()


def main(argv=None):
    """Entry point for poseur.

    Args:
        argv (Optional[List[str]]): CLI arguments

    :Environment Variables:
     - :envvar:`POSEUR_QUIET` -- same as the ``--quiet`` option in CLI
     - :envvar:`POSEUR_CONCURRENCY` -- same as the ``--concurrency`` option in CLI
     - :envvar:`POSEUR_DO_ARCHIVE` -- same as the ``--no-archive`` option in CLI (logical negation)
     - :envvar:`POSEUR_ARCHIVE_PATH` -- same as the ``--archive-path`` option in CLI
     - :envvar:`POSEUR_SOURCE_VERSION` -- same as the ``--source-version`` option in CLI
     - :envvar:`POSEUR_LINESEP` -- same as the ``--linesep`` option in CLI
     - :envvar:`POSEUR_INDENTATION` -- same as the ``--indentation`` option in CLI
     - :envvar:`POSEUR_PEP8` -- same as the ``--no-pep8`` option in CLI (logical negation)

    """
    parser = get_parser()
    args = parser.parse_args(argv)

    options = {
        'source_version': args.source_version,
        'linesep': args.linesep,
        'indentation': args.indentation,
        'pep8': args.pep8,
    }

    # check if running in simple mode
    if args.simple_args is not None:
        if args.files:
            parser.error('no Python source files or directories shall be given as positional arguments in simple mode')
        if not args.simple_args:  # read from stdin
            code = sys.stdin.read()
        else:  # read from file
            filename = args.simple_args
            options['filename'] = filename
            with open(filename, 'rb') as file:
                code = file.read()
        sys.stdout.write(convert(code, **options))  # print conversion result to stdout
        return

    # get options
    quiet = _get_quiet_option(args.quiet)
    processes = _get_concurrency_option(args.concurrency)
    do_archive = _get_do_archive_option(args.do_archive)
    archive_path = _get_archive_path_option(args.archive_path)

    # check if doing recovery
    if args.recover_file:
        recover_files(args.recover_file)
        if not args.quiet:
            print('Recovered files from archive: %r' % args.recover_file, file=sys.stderr)
        # TODO: maybe implement deletion in bpc-utils?
        if args.r2 or args.r3:
            os.remove(args.recover_file)
            if args.r3:
                archive_dir = os.path.dirname(os.path.realpath(args.recover_file))
                if not os.listdir(archive_dir):
                    os.rmdir(archive_dir)
        return

    # fetch file list
    if not args.files:
        parser.error('no Python source files or directories are given')
    filelist = sorted(detect_files(args.files))

    # terminate if no valid Python source files detected
    if not filelist:
        if not args.quiet:
            # TODO: maybe use parser.error?
            print('Warning: no valid Python source files found in %r' % args.files, file=sys.stderr)
        return

    # make archive
    if do_archive and not args.dry_run:
        archive_files(filelist, archive_path)

    # process files
    options.update({
        'quiet': quiet,
        'dry_run': args.dry_run,
    })
    map_tasks(do_poseur, filelist, kwargs=options, processes=processes)


if __name__ == '__main__':
    sys.exit(main())
