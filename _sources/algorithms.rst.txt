Algorithms
==========

As discussed in :pep:`570`, *positional-only parameters* syntax is a way to indicate
positional-only parameters in addition to *keyword-only parameters* and
*positional-or-keyword parameters*, using the notation ``/`` in the parameter list.
It can be *optional* and not so critical to developers, thus such syntax can simply
by dismissed for compatibility with older Python versions.

Basic Concepts
--------------

To convert, ``poseur`` will first extract all *positional-only parameters* from the
:term:`function` parameter list, then add a :term:`decorator` to the  original
:term:`function` definition with these parameters for runtime checks.

For example, with the samples from :pep:`570`:

.. code-block:: python

   def name(p1, p2, /, p_or_kw, *, kw): ...

it should be converted to

.. code-block:: python

   @decorator('p1', 'p2')
   def name(p1, p2, p_or_kw, *, kw): ...

Definition of the :term:`decorator` can be found as :func:`poseur.decorator`,
which takes a list of strings as names of the *positional-only parameters*.

Runtime Decorator
~~~~~~~~~~~~~~~~~

The definition of the :term:`decorator` can be described as below:

.. code-block:: python

   def decorator(*poseur):
       """Positional-only parameters runtime checker.

           Args:
               *poseur: Name list of positional-only parameters.

           Raises:
               TypeError: If any position-only parameters were passed as
                   keyword parameters.

           The decorator function may decorate regular :term:`function` and/or
           :term:`lambda` function to provide runtime checks on the original
           positional-only parameters.

       """
       import functools
       def caller(func):
           @functools.wraps(func)
           def wrapper(*args, **kwargs):
               poseur_args = set(poseur).intersection(kwargs)
               if poseur_args:
                   raise TypeError('%s() got some positional-only arguments passed as keyword arguments: %r' % (func.__name__, ', '.join(poseur_args)))
               return func(*args, **kwargs)
           return wrapper
       return caller

which will mimic the actual behaviour of the Python compiler and raises
:exc:`TypeError` if any *positional-only parameters* are provided as
*keyword parameters*.

Formatted String Literals
~~~~~~~~~~~~~~~~~~~~~~~~~

Since Python 3.6, formatted string literals (:term:`f-string`) were introduced in
:pep:`498`. And since Python 3.8, *f-string debugging syntax* were added to the grammar.
However, when ``poseur`` performs the conversion on *positional-only parameters* inside
:term:`f-string`s, it may break the lexical grammar and/or the original context.

Therefore, we utilise :mod:`f2format` to first expand such :term:`f-string`s into
:meth:`str.format` calls, then rely on ``poseur`` to perform the conversion and processing.
Basically, there are two cases as below:

1. When a :term:`lambda` with *positional-only parameters* is in a *debug* :term:`f-string`.
   (To prevent the converted code from changing the original expression for self-documenting
   and debugging.)
2. When *positional-only parameters* is in an :term:`f-string` and the runtime checks
   :term:`decorator` is to be added. (To prevent the converted code from breaking the quotes
   of the original string.)

Class Identifiers
~~~~~~~~~~~~~~~~~

In some corner cases, as all identifiers must be *mangled* and *normalised* in a
:term:`class` context, names of the extracted *positional-only parameters* will
have to be processed before putting into the parameter list of the :term:`decorator`.

Lambda Functions
----------------

:term:`lambda` functions are alike regular :term:`function`, except that we cannot add
a :term:`decorator` to its definition, but we add simply put the :term:`lambda` definition
inside a pair of parentheses ``()`` as an argument to the :term:`decorator` function.

For a sample :term:`lambda` function as follows:

.. code-block:: python

   lambda p1, p2, /, p_or_kw, *, kw: ...

``poseur`` will convert the code as below:

.. code-block:: python

   decorator('p1', 'p2')(lambda p1, p2, p_or_kw, *, kw: ...)
