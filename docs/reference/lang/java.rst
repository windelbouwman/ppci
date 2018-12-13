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

Load a class file dynamically
-----------------------------

Given that you created a class file with a static function
my_add in it, you could do the following:

.. code:: python

    >>> from ppci.arch.jvm import load_class
    >>> klass = load_class('add.class')
    >>> klass.my_add(1, 5)
    7

This example is located in the file examples/java/load.py

Links to similar projects
-------------------------

* pyjvm
  https://github.com/andrewromanenco/pyjvm

* pyjvm
  https://github.com/ronyhe/pyjvm

* jawa
  https://github.com/TkTech/Jawa

Module reference
----------------

.. automodule:: ppci.arch.jvm
    :members:

.. automodule:: ppci.arch.jvm.io
    :members:
