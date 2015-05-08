
Quickstart
==========

This is a quick guide for the impatient, to try out what you can do with the
ppci project.

Install ppci in a virtual environment:

.. code:: bash

    $ python -m venv sandbox
    $ source sandbox/bin/activate
    (sandbox) $ pip install ppci
    (sandbox) $ ppci-build.py -h


If ppci installed correcly, you will get a help message.

Download the examples bundle project here :download:`examples.zip`.

Unzip the examples and build the blinky project.

.. code:: bash

    (sandbox) $ unzip examples.zip
    (sandbox) $ ppci-build.py -f examples/blinky/build.xml
    ...
    (sandbox) $ ls examples/blinky/blinky.hex

Flash the hexfile using your flashtool of choice on the stm32f4discovery board
and enjoy the magic.


