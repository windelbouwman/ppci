
Instruction selection
~~~~~~~~~~~~~~~~~~~~~

The instruction selection phase takes care of scheduling and instruction
selection.  The output of this phase is a one frame per function with a flat
list of abstract machine instructions.


To select instruction, a tree rewrite system is used. This is also called
bottom up rewrite generator (BURG). See pyburg.

.. automodule:: ppci.codegen.instructionselector
    :members:

