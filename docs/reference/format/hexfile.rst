
Hexfile manipulation
====================

.. doctest::

    >>> from ppci.format.hexfile import HexFile
    >>> h = HexFile()
    >>> h.add_region(0, bytes([1, 2, 3]))
    >>> h.add_region(0x100, 'Hello world of hex'.encode('utf8'))
    >>> h
    Hexfile containing 21 bytes
    >>> h.dump()
    Hexfile containing 21 bytes
    Region at 0x00000000 of 3 bytes
    00000000  01 02 03                                          |...|
    Region at 0x00000100 of 18 bytes
    00000100  48 65 6c 6c 6f 20 77 6f  72 6c 64 20 6f 66 20 68  |Hello.world.of.h|
    00000110  65 78                                             |ex|


Reference
---------

.. automodule:: ppci.format.hexfile
    :members:
