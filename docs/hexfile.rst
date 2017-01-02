
Hexfile manipulation
--------------------

.. automodule:: ppci.utils.hexfile


.. doctest::

    >>> from ppci.utils.hexfile import HexFile
    >>> h = HexFile()
    >>> h.dump()
    Hexfile containing 0 bytes
    >>> h.add_region(0, bytes([1,2,3]))
    >>> h
    Hexfile containing 3 bytes
