
Backends
========

.. _mos6500:

6500
----

Status: 1%



.. _arm:

arm
---

Status: 70%

.. automodule:: ppci.arch.arm

.. autoclass:: ppci.arch.arm.ArmTarget



.. _avr:

avr
---

Status: 20%

.. autoclass:: ppci.arch.avr.AvrTarget




.. _msp430:

msp430
------

Status: 20%

.. autoclass:: ppci.arch.msp430.Msp430Target


.. _riscv:

risc-v
------

Status: 30%

Contributed by Michael.



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

.. autoclass:: ppci.arch.x86_64.X86_64Target

