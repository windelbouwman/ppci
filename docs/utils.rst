
Utilities
=========

Hexfile manipulation
--------------------


.. autoclass:: ppci.utils.hexfile.HexFile


>>> from utils import HexFile
>>> h = HexFile()
>>> h.dump()
Hexfile containing 0 bytes
>>> h.addRegion(0, bytes([1,2,3]))
>>> h
Hexfile containing 3 bytes


Yacc
----

// .. automodule:: yacc


Burg
----

.. automodule:: ppci.pyburg

