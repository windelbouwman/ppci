
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

Code generator
~~~~~~~~~~~~~~

.. automodule:: ppci.codegen.codegen

.. uml:: ppci.codegen.codegen


Canonicalize
~~~~~~~~~~~~

During this phase, the IR-code is made simpler. Also unsupported
operations are rewritten into function calls. For example soft floating
point is introduced here.


Tree building
~~~~~~~~~~~~~

From IR-code a tree is generated which can be used to select instructions.

.. automodule:: ppci.codegen.irdag


Instruction selection
~~~~~~~~~~~~~~~~~~~~~

The instruction selection phase takes care of scheduling and instruction
selection.  The output of this phase is a one frame per function with a flat
list of abstract machine instructions.


To select instruction, a tree rewrite system is used. This is also called
bottom up rewrite generator (BURG). See pyburg.


Register allocation
~~~~~~~~~~~~~~~~~~~

.. automodule:: ppci.codegen.registerallocator

code emission
~~~~~~~~~~~~~

Code is emitted using the outputstream class. The assembler and compiler use
this class to emit instructions to. The stream can output to object file
or to a logger.

.. autoclass:: ppci.binutils.outstream.OutputStream
