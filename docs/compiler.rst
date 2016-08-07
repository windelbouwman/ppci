


Compiler internals
==================

This chapter describes the design of the compiler.
The compiler consists a frontend, mid-end and back-end. The frontend deals with
source file parsing and semantics checking. The mid-end performs optimizations.
This is optional. The back-end generates machine code. The front-end produces
intermediate code. This is a simple representation of the source. The back-end
can accept this kind of representation.

The compiler is greatly influenced by the `LLVM`_ design.

.. _llvm: http://www.llvm.org

.. graphviz::

   digraph x {
   rankdir="LR"
   1 [label="c3 source file"]
   10 [label="c3 front end" ]
   11 [label="language X front end" ]
   20 [label="mid end" ]
   30 [label="back end for X86" ]
   31 [label="back end for ARM" ]
   40 [label="object file"]
   1 -> 10
   10 -> 20 [label="IR-code"]
   11 -> 20 [label="IR-code"]
   20 -> 30 [label="IR-code"]
   20 -> 31 [label="IR-code"]
   30 -> 40
   }


.. toctree::

    compiler/frontends
    compiler/backend
    compiler/optimization
    compiler/specificationlang



IR-code
-------

The intermediate representation (IR) of a program de-couples the front end
from the backend of the compiler.

See :doc:`ir` for details about all the available instructions.


