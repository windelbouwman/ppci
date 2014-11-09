

About
=====

The pure-python-compiler-infrastructure (ppci) is a compiler suite written in
pure python. The project contains the following:

- Language front-ends: Brainfuck, C3
- Various code optimizers
- Backends for various platforms: ARM, Thumb, Python
- Assembler
- Linker

**Warning: This project is in pre-alpha state and not for use in production!**

ppci can be installed using pip:

.. code:: bash

    $ pip install ppci


Sourcecode is located here:

- https://bitbucket.org/windel/ppci
- https://pikacode.com/windel/ppci/


Documentation can be found on read the docs: http://ppci.readthedocs.org/


+-------------------------------+---------------------------------------------+
| Topic                         | Status                                      |
+===============================+=============================================+
| C3 language front-end         | Fairly complete                             |
+-------------------------------+---------------------------------------------+
| Brainfuck language front-end  | Working                                     |
+-------------------------------+---------------------------------------------+
| ARM code generation           | Bare minimum for hello world                |
+-------------------------------+---------------------------------------------+
| Thumb code generation         | Bare minimum for blinky on stm32f4discovery |
+-------------------------------+---------------------------------------------+
| Build status                  | |dronestate|_                               |
+-------------------------------+---------------------------------------------+
| Development status            | |devstate|_                                 |
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


.. |docstate| image:: https://readthedocs.org/projects/ppci/badge/?version=latest
.. _docstate: https://ppci.readthedocs.org/en/latest
