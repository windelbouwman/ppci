
Quickstart
==========

Install ppci in a virtual environment:

.. code:: bash

    $ python -m venv sandbox
    $ source sandbox/bin/activate
    (sandbox) $ pip install ppci
    (sandbox) $ ppci-build.py -h


If ppci installed correcly, you will get a help message.

Download and unzip the examples bundle project here :download:`examples.zip`.


stm32f4 example
---------------

To build the blinky project do the following:

.. code:: bash

    $ cd examples/blinky
    $ ppci-build.py

Flash the hexfile using your flashtool of choice on the stm32f4discovery board
and enjoy the magic.

arduino example
---------------

To build and the arduino blink led example, follow the following commands:

.. code:: bash

    $ cd examples/arduino
    $ ppci-build.py
    $ avrdude -v -P /dev/ttyACM0 -c arduino -p m328p -U flash:w:blinky.hex

