
About
=====

This The pure-python-compiler-infrastruce (ppci).
This project aims to implement a compiler toolset in pure python.

Installation
============

ppci can be installed from mercurial by using pip (virtualenv is recommended)

.. code:: bash

  pip install hg+https://bitbucket.org/windel/ppci


Status
======

+------------------------+---------------------------------------------+
| Topic                  | Status                                      |
+========================+=============================================+
| C3 language front-end  | Fairly complete                             |
+------------------------+---------------------------------------------+
| ARM code generation    | Bare minimum for hello world                |
+------------------------+---------------------------------------------+
| Thumb code generation  | Bare minimum for blinky on stm32f4discovery |
+------------------------+---------------------------------------------+
| Build status           | |dronestate|_                               |
+------------------------+---------------------------------------------+
| Documentation          | |docstate|_                                 |
+------------------------+---------------------------------------------+


.. |dronestate| image:: https://drone.io/bitbucket.org/windel/ppci/status.png
.. _dronestate: https://drone.io/bitbucket.org/windel/ppci


.. |docstate| image:: https://readthedocs.org/projects/ppci/badge/?version=latest
.. _docstate: https://ppci.readthedocs.org/en/latest
