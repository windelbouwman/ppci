
Language tools
==============

The :py:mod:`ppci.lang.tools` package contains tools for programming language
construction.

Diagnostics
-----------

To provide useful feedback about programming errors, there are classes for
sourcecode location and diagnostics.

.. automodule:: ppci.lang.common
    :members:

Lexing
------

.. automodule:: ppci.lang.tools.baselex
    :members:


Grammar
-------

To help to define a grammar for a language the grammar classes can be used
to define a language grammar. From this grammar parsers can be generated.

A grammar can be defined like this:

.. doctest::

   >>> from ppci.lang.tools.grammar import Grammar
   >>> g = Grammar()
   >>> g.add_terminal('term')
   >>> g.add_production('expr', ['expr', '+', 'term'])
   >>> g.add_production('expr', ['expr', '-', 'term'])
   >>> g.dump()
   Grammar with 2 rules and 1 terminals
   expr -> ('expr', '+', 'term') P_0
   expr -> ('expr', '-', 'term') P_0
   >>> g.is_terminal('expr')
   False
   >>> g.is_terminal('term')
   True

.. automodule:: ppci.lang.tools.grammar
    :members:

Earley parser
-------------

.. automodule:: ppci.lang.tools.earley
    :members:

Recursive descent
-----------------

Recursive descent parsing (also known as handwritten parsing) is an
easy way to parse sourcecode.

.. automodule:: ppci.lang.tools.recursivedescent
    :members:

LR parsing
----------

.. automodule:: ppci.lang.tools.lr
    :members:

.. automodule:: ppci.lang.tools.yacc
    :members:
