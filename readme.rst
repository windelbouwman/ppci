
About
=====

This The pure-python-compiler-infrastructure (ppci). This project aims to
implement a compiler toolset in python. As of now, the library can generate
arm thumb code and arm code.

Installation
============

ppci can be installed from mercurial by using pip with virtualenv:

.. code:: bash

    $ cd ~
    $ virtuelenv ppci_sandbox
    $ source ppci_sandbox/bin/activate
    (ppci_sandbox)$ pip install hg+https://bitbucket.org/windel/ppci
    (ppci_sandbox)$ zcc.py -h
    (ppci_sandbox)$ deactivate
    $

Source
======

Sourcecode is located at bitbucket:

https://bitbucket.org/windel/ppci

Documentation
=============

Documentation can be found on read the docs: http://ppci.readthedocs.org/


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
