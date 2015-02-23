
Build system
============

It can be convenient to bundle a series of build steps into a script, for
example a makefile. Instead of depending on make, yet another build tool
was created. The build specification is specified in xml. Much like msbuild
and Ant.

A project can contain a build.xml
file which describes how the project should be build.

For example:

.. literalinclude:: ../examples/build.xml
    :language: xml
    :linenos:
