Java
====

.. warning::

    This module is a work in progress.

Java a perhaps the most used programming language in the world.

There are some functions to deal with jar-files.

Compile java ahead of time
--------------------------

One could do this. Say, we have some java code:

.. code:: java

   class Test14 {
       static int my_add(int a, int b) {
           return a + b + 1;
       }
   }

We can compile this with javac, and next up, compile it with ppci into msp430
code:

.. code:: bash

    $ javac Test14.java
    $ python -m ppci.cli.java compile Test14.class -m msp430


Module reference
----------------

.. automodule:: ppci.arch.jvm
    :members:

.. automodule:: ppci.arch.jvm.io
    :members:
