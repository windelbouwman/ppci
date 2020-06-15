
Quickstart
==========

Installation
------------

Using pip
~~~~~~~~~

Install ppci in a `virtualenv`_ environment:

.. _virtualenv: https://virtualenv.readthedocs.io/

.. code:: bash

    $ virtualenv sandbox
    $ source sandbox/bin/activate
    (sandbox) $ pip install ppci
    (sandbox) $ ppci-build -h


If ppci installed correcly, you will get a help message of the
:ref:`ppci-build` commandline tool.

Manually
~~~~~~~~

Alternatively you can download a zip package from
`PyPI <https://pypi.python.org/pypi/ppci>`_
or from `BitBucket <https://bitbucket.org/windel/ppci>`_.
Unpack the source archive and open a console in this directory.

.. code:: bash

    $ virtualenv sandbox
    $ source sandbox/bin/activate
    (sandbox) $ python setup.py install
    (sandbox) $ ppci-build -h

If ppci installed correcly, you will get a help message of the
:ref:`ppci-build` commandline tool.

Compile some code!
------------------

Now lets compile some code via the :ref:`high level api functions<api>`:

.. doctest::

    >>> import io
    >>> from ppci.api import cc, get_arch
    >>> source = "int add(int a, int b) { return a + b; }"
    >>> f = io.StringIO(source)
    >>> obj = cc(f, get_arch('arm'))
    >>> obj
    CodeObject of 48 bytes

Let review what we have just done:

- We defined a simple add function in C
- We compiled this with the :func:`ppci.api.cc` function to arm object code

Example projects
----------------

The `examples folder in the ppci sourcecode <https://bitbucket.org/windel/ppci/src/default/examples/>`_ contains some demo projects
that can be built using PPCI.


**stm32f4 example**


To build the blinky project do the following:

.. code:: bash

    $ cd examples/blinky
    $ ppci-build

Flash the hexfile using your flashtool of choice on the stm32f4discovery board
and enjoy the magic.

**arduino example**

To build and flash the arduino blink led example, use the following commands:

.. code:: bash

    $ cd examples/avr/arduino-blinky
    $ ppci-build
    $ avrdude -v -P /dev/ttyACM0 -c arduino -p m328p -U flash:w:blinky.hex


**Linux x86_64 example**

To build the hello world for 64-bit linux, go here:

.. code:: bash

    $ cd examples/linux64/hello
    $ ppci-build
    $ ./hello

Or run the snake demo under linux:

.. code:: bash

    $ cd examples/linux64/snake
    $ ppci-build
    $ ./snake


Next steps
----------

If you have checked out the examples, head over to the
:doc:`howto<howto/index>`,
:doc:`api<reference/api>` and :doc:`reference<reference/index>`
sections to learn more!
