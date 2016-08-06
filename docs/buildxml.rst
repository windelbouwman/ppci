
Build system
============

It can be convenient to bundle a series of build steps into a script, for
example a makefile. Instead of depending on make, yet another build tool
was created. The build specification is specified in xml. Much like msbuild
and Ant.

A project can contain a build.xml
file which describes how the project should be build. The name of the file
can be build.xml or another filename. This file can than be given
to :ref:`ppci-build`.

An example build file:

.. literalinclude:: ../examples/lm3s6965evb/snake/build.xml
    :language: xml
    :linenos:

Projects
--------

The root element of a build file is the project tag. This tag
contains a name and optionally a default target attribute.
When no target is given when building the project, the default
target is selected.

Targets
-------

Like make, targets can depend on eachother. Then one target is
run, the build system makes sure to run depending targets first.
Target elements contain a list of tasks to perform.


Tasks
-----

The task elements are contained within target elements.
Each task specifies a build action. For example the link
task takes multiple object files and combines those into
a merged object.


