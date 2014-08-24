
St link
=======


Programming the stm32f4 discovery board.

Getting the example code
------------------------

Change into your home directory and checkout the ppci source code:

.. code:: bash

    $ cd ~
    $ mkdir HG
    $ cd HG
    $ hg clone https://bitbucket.org/windel/ppci

If everything went well, you now have the latest version of ppci checked out.

Building
--------

Compiling the stm32f4xx example project using the compiler toolchain:

.. code:: bash

    $ cd ~/HG/ppci/test/data/stm32f4xx
    $ zcc.py build
      2014-08-15 12:40:15,640|INFO|taskrunner|Target sequence: [Target "burn2", Target "all"]
      2014-08-15 12:40:15,640|INFO|taskrunner|Target burn2
      2014-08-15 12:40:15,640|INFO|taskrunner|Running Task "AssembleTask"
      2014-08-15 12:40:15,641|INFO|taskrunner|Running Task "C3cTask"
      2014-08-15 12:40:15,705|INFO|taskrunner|Running Task "LinkTask"
      2014-08-15 12:40:15,710|INFO|taskrunner|Running Task "ObjCopyTask"
      2014-08-15 12:40:15,711|INFO|taskrunner|Target all
      2014-08-15 12:40:15,711|INFO|taskrunner|Done!
    $ ls -latr
      burn2.hex

Flashing
--------

First inspect the hexfile you want to flash with the hexutil program:

.. code:: bash

    $ hexutil.py info ~/HG/ppci/test/data/stm32f4xx/burn2.hex
      Hexfile containing 408 bytes
      Region at 0x08000000 of 408 bytes


To flash an application using the st-link V2 debugger, use the st-flash
program:

.. code:: bash

    $ st-flash.py hexwrite burn2.hex
      flashing Region at 0x08000000 of 408 bytes

