API Reference
=============

.. module:: poseur

.. .. automodule:: poseur
..    :members:
..    :undoc-members:
..    :show-inheritance:

Public Interface
----------------

.. autofunction:: poseur.convert

.. autofunction:: poseur.poseur

.. autofunction:: poseur.main

Runtime Decorator
-----------------

As you may wish to provide runtime positional-only parameter checks for
your own code, ``poseur`` exposed the :term:`decorator` function for
developers to use by themselves.

.. autofunction:: poseur.decorator

Conversion Implementation
-------------------------

The main logic of the ``poseur`` conversion is to extract all *positional-only
parameters* and add a **:term:`decorator`** for the :term:`function` and/or :term:`lambda`
definition to provide runtime checks with the extracted parameters.

For conversion algorithms and details, please refer to :doc:`algorithms`.

Data Structures
~~~~~~~~~~~~~~~

During conversion, we utilised :class:`bpc_utils.Config` to store and deliver the
configurations over the conversion :class:`~poseur.Context` instances, which should
be as following:

.. class:: Config

   Configuration object shared over the conversion process of a single source file.

   .. attribute:: indentation
      :type: str

      Indentation sequence.

   .. attribute:: linesep
      :type: Literal[\'\\n\', \'\\r\\n\', \'\\r\']

      Line separator.

   .. attribute:: pep8
      :type: bool

      :pep:`8` compliant conversion flag.

   .. attribute:: filename
      :type: Optional[str]

      An optional source file name to provide a context in case of error.

   .. attribute:: source_version
      :type: Optional[str]

      Parse the code as this Python version (uses the latest version by default).

   .. attribute:: decorator
      :type: str

      Name of the :term:`decorator` function for runtime checks on original
      *positional-only parameters*.

   .. attribute:: dismiss
      :type: bool

      Flag if integrate runtime checks, i.e. the :term:`decorator` function,
      on original *positional-only parameters*.

Conversion Templates
~~~~~~~~~~~~~~~~~~~~

For general conversion scenarios, the :term:`decorator` function will be
rendered based on the following templates.

.. data:: DECORATOR_TEMPLATE
   :type: List[str]

   .. code-block:: python

      ['def %(decorator)s(*poseur):',
       '%(indentation)s"""Positional-only parameters runtime checker.',
       '%(indentation)s',
       '%(indentation)s    Args:',
       '%(indentation)s        *poseur: Name list of positional-only parameters.',
       '%(indentation)s',
       '%(indentation)s    Raises:',
       '%(indentation)s        TypeError: If any position-only parameters were passed as',
       '%(indentation)s            keyword parameters.',
       '%(indentation)s',
       '%(indentation)s    The decorator function may decorate regular :term:`function` and/or',
       '%(indentation)s    :term:`lambda` function to provide runtime checks on the original',
       '%(indentation)s    positional-only parameters.',
       '%(indentation)s',
       '%(indentation)s"""',
       '%(indentation)simport functools',
       '%(indentation)sdef caller(func):',
       '%(indentation)s%(indentation)s@functools.wraps(func)',
       '%(indentation)s%(indentation)sdef wrapper(*args, **kwargs):',
       '%(indentation)s%(indentation)s%(indentation)sposeur_args = set(poseur).intersection(kwargs)',
       '%(indentation)s%(indentation)s%(indentation)sif poseur_args:',
       "%(indentation)s%(indentation)s%(indentation)s%(indentation)sraise TypeError('%%s() got some positional-only arguments passed as keyword arguments: %%r' %% (func.__name__, ', '.join(poseur_args)))",
       '%(indentation)s%(indentation)s%(indentation)sreturn func(*args, **kwargs)',
       '%(indentation)s%(indentation)sreturn wrapper',
       '%(indentation)sreturn caller']

   Decorator function to provide runtime checks on the original
   *positional-only parameters*.

   :Variables:
      * **decorator** -- :term:`decorator` function name as defined in
        :attr:`Config.decorator <poseur.Config.decorator>`
      * **indentation** -- indentation sequence as defined in
        :attr:`Config.indentation <poseur.Config.indentation>`

   .. important::

      Actually, the :func:`poseur.decorator` function is rendered and
      evaluated at runtime using this template.

Conversion Contexts
~~~~~~~~~~~~~~~~~~~

.. autoclass:: poseur.Context
   :members:
   :undoc-members:
   :private-members:
   :show-inheritance:

.. autoclass:: poseur.StringContext
   :members:
   :undoc-members:
   :private-members:
   :show-inheritance:

Internal Auxiliaries
--------------------

Options & Defaults
~~~~~~~~~~~~~~~~~~

.. autodata:: poseur.POSEUR_SOURCE_VERSIONS

Below are option getter utility functions. Option value precedence is::

   explicit value (CLI/API arguments) > environment variable > default value

.. autofunction:: poseur._get_quiet_option
.. autofunction:: poseur._get_concurrency_option
.. autofunction:: poseur._get_do_archive_option
.. autofunction:: poseur._get_archive_path_option
.. autofunction:: poseur._get_source_version_option
.. autofunction:: poseur._get_linesep_option
.. autofunction:: poseur._get_indentation_option
.. autofunction:: poseur._get_pep8_option

The following variables are used for fallback default values of options.

.. autodata:: poseur._default_quiet
.. autodata:: poseur._default_concurrency
.. autodata:: poseur._default_do_archive
.. autodata:: poseur._default_archive_path
.. autodata:: poseur._default_source_version
.. autodata:: poseur._default_linesep
.. autodata:: poseur._default_indentation
.. autodata:: poseur._default_pep8

.. important::

   For :data:`_default_concurrency`, :data:`_default_linesep` and :data:`_default_indentation`,
   :data:`None` means *auto detection* during runtime.

CLI Utilities
~~~~~~~~~~~~~

.. autofunction:: poseur.get_parser

The following variables are used for help messages in the argument parser.

.. data:: poseur.__cwd__
   :type: str

   Current working directory returned by :func:`os.getcwd`.

.. data:: poseur.__poseur_quiet__
   :type: Literal[\'quiet mode\', \'non-quiet mode\']

   Default value for the ``--quiet`` option.

   .. seealso:: :func:`poseur._get_quiet_option`

.. data:: poseur.__poseur_concurrency__
   :type: Union[int, Literal[\'auto detect\']]

   Default value for the ``--concurrency`` option.

   .. seealso:: :func:`poseur._get_concurrency_option`

.. data:: poseur.__poseur_do_archive__
   :type: Literal[\'will do archive\', \'will not do archive\']

   Default value for the ``--no-archive`` option.

   .. seealso:: :func:`poseur._get_do_archive_option`

.. data:: poseur.__poseur_archive_path__
   :type: str

   Default value for the ``--archive-path`` option.

   .. seealso:: :func:`poseur._get_archive_path_option`

.. data:: poseur.__poseur_source_version__
   :type: str

   Default value for the ``--source-version`` option.

   .. seealso:: :func:`poseur._get_source_version_option`

.. data:: poseur.__poseur_linesep__
   :type: Literal[\'LF\', \'CRLF\', \'CR\', \'auto detect\']

   Default value for the ``--linesep`` option.

   .. seealso:: :func:`poseur._get_linesep_option`

.. data:: poseur.__poseur_indentation__
   :type: str

   Default value for the ``--indentation`` option.

   .. seealso:: :func:`poseur._get_indentation_option`

.. data:: poseur.__poseur_pep8__
   :type: Literal[\'will conform to PEP 8\', \'will not conform to PEP 8\']

   Default value for the ``--no-pep8`` option.

   .. seealso:: :func:`poseur._get_pep8_option`
