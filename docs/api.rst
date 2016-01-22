
Api
===

Instead of using the :doc:`commandline<usage>`, it is also possible to use
ppci api.
For
example to assemble, compile, link and objcopy the msp430 blinky example
project:

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


api module
----------

.. automodule:: ppci.api
   :members:
