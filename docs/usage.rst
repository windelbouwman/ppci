
Usage
=====

This section describes the usage of the user tools.

Project structure
-----------------

The structure of a project is very simple. Every project contains a build.xml
file which describes how the project should be build. This format is more
or less taken from ant build files, which are also described using xml.

Take for example the stm32f4 led project build file:

.. literalinclude:: ../test/data/stm32f4xx/build.xml
    :language: xml
    :linenos:


Building
--------

To build the project, run zcc.py in the same directory:

.. code:: bash

    $ zcc.py

Or specify the buildfile:

.. code:: bash

    $ zcc.py -b test/data/stm32f4xx/build.xml


