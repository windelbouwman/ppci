
Command line tools
==================

This section describes the usage of some commandline tools installed with ppci.


ppci-build.py
-------------

It can be convenient to bundle a series of build steps into a script, for
example a makefile. This utility can be used to build entire
projects defined by a build.xml file.
Every project contains a build.xml
file which describes how the project should be build. This format is more
or less taken from ant build files, which are also described using xml.

Take for example the stm32f4 led project build file:

.. literalinclude:: ../test/data/stm32f4xx/build.xml
    :language: xml
    :linenos:


To build the project, run zcc.py in the same directory:

.. code:: bash

    $ cd test/data/stm32f4xx
    $ ppci-build.py

Or specify the buildfile:

.. code:: bash

    $ ppci-build.py -f test/data/stm32f4xx/build.xml

