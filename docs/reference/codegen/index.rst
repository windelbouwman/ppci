
.. module:: ppci.codegen

Code generation
===============

The module :mod:`ppci.codegen` provides functions and classes to generate
code.

.. _codegen:

Back-end
--------

The back-end is more complicated. There are several steps to be taken here.

#. Tree creation
#. Instruction selection
#. Register allocation
#. Peep hole optimization

.. graphviz::
 
   digraph codegen {
   1 [label="IR-code"]

   10 [label="irdag"]
   20 [label="dagsplitter"]
   30 [label="instruction selector"]
   40 [label="register allocator"]

   49 [label="assembly parser"]
   50 [label="outstream"]
   60 [label="object file"]
   61 [label="text output"]
   1 -> 10
   10 -> 20 [label="Selection DAG"]
   20 -> 30 [label="Selection Trees"]
   30 -> 40 [label="frame"]
   40 -> 50 [label="frame"]

   49 -> 50
   50 -> 60
   50 -> 61
   }

Canonicalize
~~~~~~~~~~~~

During this phase, the IR-code is made simpler. Also unsupported
operations are rewritten into function calls. For example soft floating
point is introduced here.

.. toctree::

    codegen
    instructionselection
    registerallocator
    outstream
    dagsplit
