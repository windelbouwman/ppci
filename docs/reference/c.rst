
C classes
=========

The C frontend can be used to generate an AST from C code. You can use
it to parse C code and analyze its structure like this:

.. doctest::

    >>> from ppci.api import get_arch
    >>> from ppci.lang.c import create_ast
    >>> src = "int a, *b;"
    >>> ast = create_ast(src, get_arch('msp430'))
    >>> ast
    Compilation unit with 2 declarations
    >>> from ppci.lang.c import CAstPrinter
    >>> printer = CAstPrinter()
    >>> printer.print(ast)
    Compilation unit with 2 declarations
      Variable [storage=None typ=Native type int name=a]
        Native type int
      Variable [storage=None typ=Pointer-type name=b]
        Pointer-type
          Native type int
    >>> ast.declarations[0].name
    'a'


Module reference
----------------

.. autoclass:: ppci.lang.c.CParser
    :members:

.. autoclass:: ppci.lang.c.CSemantics
    :members:


Uml
---

.. uml:: ppci.lang.c.types

.. uml:: ppci.lang.c.expressions

.. uml:: ppci.lang.c.statements
