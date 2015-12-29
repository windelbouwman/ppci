
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
    $ ls blinky.hex

Flash the hexfile using your flashtool of choice on the stm32f4discovery board
and enjoy the magic.

arduino example
---------------

To build the arduino blink led example, first build the example:

.. code:: bash

    $ cd examples/arduino
    $ ppci-build.py

Next flash the hexfile using avrdude for example:

.. code:: bash

    $ avrdude -v -P /dev/ttyACM0 -c arduino -p m328p -U flash:w:blinky.hex

