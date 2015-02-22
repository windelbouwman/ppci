

Introduction
============

The ppci project is a compiler, assembler, linker and build-system written 
entirely in
python. The project contains everything from language front-end to code
generation.
It contains a front-end for the c3 language, can optimize this code
and generate ARM-code.

The project contains the following:

- Language front-ends: Brainfuck, :doc:`c3`
- Various code optimizers
- Backends for various platforms: ARM, Thumb, Python
- Assembler
- Linker

**Warning: This project is in alpha state and not read for production use!**

Quick guide
-----------

ppci can be installed using pip:

.. code:: bash

    $ pip install ppci

To invoke the builder and compile the snake demo, use the following:

.. code:: bash

    $ ppci-build.py -f examples/build.xml

If the compilation was succesful, the snake demo compiled into
'examples/snake.bin'. This is a binary file with ARM-code which can be run
in qemu as follows:

.. code:: bash

    $ qemu-system-arm -M lm3s6965evb -kernel snake.bin -serial stdio

This runs the snake demo on an emulated lm3s demo board and displays
the game to the console.


Instead of using the :doc:`usage`, you can also
use the :doc:`api`.

Links
-----

Sourcecode is located here:

- https://bitbucket.org/windel/ppci
- https://pikacode.com/windel/ppci/


Documentation can be found here:

- http://ppci.readthedocs.org/


+-------------------------------+---------------------------------------------+
| Build status                  | |dronestate|_                               |
|                               | |appveyor|_                                 |
+-------------------------------+---------------------------------------------+
| Development status            | |devstate|_                                 |
+-------------------------------+---------------------------------------------+
| Open hub                      | openhub_                                    |
+-------------------------------+---------------------------------------------+
| Documentation                 | |docstate|_                                 |
+-------------------------------+---------------------------------------------+
| Current release               | |version|_                                  |
+-------------------------------+---------------------------------------------+
| Python implementations        | |pyimpls|_                                  |
+-------------------------------+---------------------------------------------+
| Python versions               | |pyversions|_                               |
+-------------------------------+---------------------------------------------+
| License                       | |license|_                                  |
+-------------------------------+---------------------------------------------+
| Downloads                     | |downloads|_                                |
+-------------------------------+---------------------------------------------+


.. _openhub: https://www.openhub.net/p/ppci

.. |downloads| image:: https://pypip.in/download/ppci/badge.svg
.. _downloads: https://pypi.python.org/pypi/ppci


.. |version| image:: https://pypip.in/version/ppci/badge.svg
.. _version: https://pypi.python.org/pypi/ppci


.. |license| image:: https://pypip.in/license/ppci/badge.svg
.. _license: https://pypi.python.org/pypi/ppci


.. |devstate| image:: https://pypip.in/status/ppci/badge.svg
.. _devstate: https://pypi.python.org/pypi/ppci


.. |pyversions| image:: https://pypip.in/py_versions/ppci/badge.svg
.. _pyversions: https://pypi.python.org/pypi/ppci


.. |pyimpls| image:: https://pypip.in/implementation/ppci/badge.svg
.. _pyimpls: https://pypi.python.org/pypi/ppci


.. |dronestate| image:: https://drone.io/bitbucket.org/windel/ppci/status.png
.. _dronestate: https://drone.io/bitbucket.org/windel/ppci


.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/h0h5huliflrac65o?svg=true
.. _appveyor: https://ci.appveyor.com/project/WindelBouwman/ppci-786


.. |docstate| image:: https://readthedocs.org/projects/ppci/badge/?version=latest
.. _docstate: https://ppci.readthedocs.org/en/latest
