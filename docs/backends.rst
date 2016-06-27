
Backends
========

This page lists the available backends.

.. _mos6500:

6500
----

Status: 1%

.. autoclass:: ppci.arch.mos6500.Mos6500Arch


.. _arm:

arm
---

Status: 70%

.. automodule:: ppci.arch.arm

.. autoclass:: ppci.arch.arm.ArmArch


.. _avr:

avr
---

.. automodule:: ppci.arch.avr


.. _msp430:

msp430
------

Status: 20%

.. autoclass:: ppci.arch.msp430.Msp430Arch


To flash the msp430 board, the following program can be used:

http://www.ti.com/tool/msp430-flasher


.. _riscv:

risc-v
------

See also: http://riscv.org

Status: 30%

Contributed by Michael.

.. autoclass:: ppci.arch.riscv.RiscvArch


.. _stm8:

stm8
----

STM8 is an 8-bit processor, see also:
http://www.st.com/stm8

Status: 0%


.. _x86_64:

x86_64
------

Status: 60%

For a good list of op codes, checkout:

http://ref.x86asm.net/coder64.html

For an online assembler, checkout:

https://defuse.ca/online-x86-assembler.htm

Linux
~~~~~

For a good list of linux system calls, refer:

http://blog.rchapman.org/post/36801038863/linux-system-call-table-for-x86-64

.. autoclass:: ppci.arch.x86_64.X86_64Arch


How to write a new backend
--------------------------

This section describes how to add a new backend. The best thing to do is
to take a look at existing backends, like the backends for ARM and X86_64.

A backend consists of the following parts:

#. register descriptions
#. instruction descriptions
#. template descriptions
#. architecture description


Register description
~~~~~~~~~~~~~~~~~~~~

A backend must describe what kinds of registers are available. To do this
define for each register class a subclass of :class:`ppci.arch.isa.Register`.

There may be several register classes, for example 8-bit and 32-bit registers.
It is also possible that these classes overlap.

.. code:: python

    from ppci.arch.isa import Register

    class X86Register(Register):
        bitsize=32

    class LowX86Register(Register):
        bitsize=8

    AL = LowX86Register('al', num=0)
    AH = LowX86Register('ah', num=4)
    EAX = X86Register('eax', num=0, aliases(AL, AH))


Architecture description
~~~~~~~~~~~~~~~~~~~~~~~~


Class reference
~~~~~~~~~~~~~~~

.. automodule:: ppci.arch

