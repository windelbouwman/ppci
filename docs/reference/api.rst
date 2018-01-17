
.. _api:

Api
===

The ppci library provides provides an intuitive api to the compiler, assembler
and other tools.
For example to assemble, compile, link and objcopy the msp430 blinky example
project, the api can be used as follows:

.. testsetup::

    import os
    os.chdir('..')

.. testcleanup::

    import os
    os.chdir('docs')

.. doctest::

    >>> from ppci.api import asm, c3c, link, objcopy
    >>> march = "msp430"
    >>> o1 = asm('examples/msp430/blinky/boot.asm', march)
    >>> o2 = c3c(['examples/msp430/blinky/blinky.c3'], [], march)
    >>> o3 = link([o2, o1], 'examples/msp430/blinky/msp430.mmap', march)
    >>> objcopy(o3, 'flash', 'hex', 'blinky_msp430.hex')

Instead of using the api, a set of :doc:`commandline tools<cli>` are also
prodived.

.. automodule:: ppci.api
   :members:
