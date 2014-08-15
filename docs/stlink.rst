
St link
=======


Programming the stm32f4 discovery board.

Building
--------

Compiling the stm32f4xx example project using the compiler toolchain:

.. code:: bash

    $ cd test/data/stm32f4xx
    $ zcc.py
    2014-08-15 11:27:48,844|INFO|taskrunner|Target sequence: [Target "burn2", Target "all"]
    2014-08-15 11:27:48,844|INFO|taskrunner|Target burn2
    2014-08-15 11:27:48,845|INFO|taskrunner|Running Task "AssembleTask"
    2014-08-15 11:27:48,845|INFO|taskrunner|Running Task "C3cTask"
    2014-08-15 11:27:48,909|INFO|taskrunner|Running Task "LinkTask"
    2014-08-15 11:27:48,915|INFO|taskrunner|Target all
    2014-08-15 11:27:48,915|INFO|taskrunner|Done!
    $ ls


Flashing
--------

To flash an application using the st-link V2 debugger, use the following
command:

.. code:: bash

    $ st-flash.py hexwrite burn2.hex

