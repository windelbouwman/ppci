
Hexfile manipulation
====================

.. doctest::

    >>> from ppci.formats.hexfile import HexFile
    >>> h = HexFile()
    >>> h.dump()
    Hexfile containing 0 bytes
    >>> h.add_region(0, bytes([1, 2, 3]))
    >>> h
    Hexfile containing 3 bytes


Reference
---------

.. automodule:: ppci.formats.hexfile
    :members:
