
S-expressions
=============

The ppci.lang.sexpr module can be used to read
`S-expressions <https://rosettacode.org/wiki/S-Expressions>`_.

.. doctest::

    >>> from ppci.lang.sexpr import parse_sexpr
    >>> s = parse_sexpr('(bla 29 ("hello world" 1337 @#!))')
    >>> s.as_tuple()
    ('bla', 29, ('hello world', 1337, '@#!'))

Reference
---------

.. automodule:: ppci.lang.sexpr
    :members:
