
Utilities
=========

Hexfile manipulation
--------------------


.. autoclass:: utils.HexFile


>>> from utils import HexFile
>>> h = HexFile()
>>> h.dump()
Hexfile containing 0 bytes
>>> h.addRegion(0, bytes([1,2,3]))
>>> h
Hexfile containing 3 bytes


Yacc
----

.. automodule:: yacc


Burg
----

.. automodule:: pyburg


Machine descriptions
--------------------

There are some attempts made already to describe machines in a Domain
Specific Language (DSL). Examples of these are:
- Tablegen (llvm)
- cgen (gnu)
- LISA (Aachen)
- nML (Berlin)
- SLED (Specifying representations of machine instructions (norman ramsey and Mary F. Fernandez))


The goal of a machine description file is to describe a file and generate
tools like assemblers, disassemblers, linkers, debuggers and simulators.

Advantage of using this approach is that porting these tools is a semi automated
process. Rewriting all of these tools from scratch is tedious and errorprone.

Concepts to use in this language:
- Single stream of instructions
- State stored in memory
- Pipelining
- Instruction semantics

Each instruction has the following properties:
- Bit representation
- Assembly language representation
- Semantic action

Optionally a description in terms of compiler code generation can be attached
to this. But perhaps this clutters the description too much and we need to put
it elsewhere.


The description language can help to expand these descriptions by expanding
the permutations.



