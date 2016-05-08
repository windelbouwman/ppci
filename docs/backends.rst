
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

Status: 20%

.. autoclass:: ppci.arch.avr.AvrArch


.. _msp430:

msp430
------

Status: 20%

.. autoclass:: ppci.arch.msp430.Msp430Arch


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

