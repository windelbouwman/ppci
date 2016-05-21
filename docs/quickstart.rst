
Quickstart
==========

Installation
------------

Install ppci in a `virtualenv`_ environment:

.. _virtualenv: https://virtualenv.readthedocs.io/

.. code:: bash

    $ virtualenv sandbox
    $ source sandbox/bin/activate
    (sandbox) $ pip install ppci
    (sandbox) $ ppci-build.py -h


If ppci installed correcly, you will get a help message of the
:ref:`ppci-build` commandline tool.


Example projects
----------------

Download and unzip :download:`examples.zip` to checkout some demo projects
that can be build using ppci.


**stm32f4 example**


To build the blinky project do the following:

.. code:: bash

    $ cd examples/blinky
    $ ppci-build.py

Flash the hexfile using your flashtool of choice on the stm32f4discovery board
and enjoy the magic.

**arduino example**

To build and the arduino blink led example, follow the following commands:

.. code:: bash

    $ cd examples/arduino
    $ ppci-build.py
    $ avrdude -v -P /dev/ttyACM0 -c arduino -p m328p -U flash:w:blinky.hex


**Linux x86_64**

Instead of for an arm or avr board you can compile into a 64-bit
linux binary:

.. code:: bash

    $ cd examples/linux64/hello
    $ ppci-build.py
    $ ./hello

Or run the snake demo under linux:

.. code:: bash

    $ cd examples/linux64/snake
    $ ppci-build.py
    $ ./snake


Next steps
----------

If you have checked out the examples, head over to the
:doc:`api<api>` and :doc:`reference<reference>`
sections to learn more!
