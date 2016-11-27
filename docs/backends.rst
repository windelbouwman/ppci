
Backends
========

This page lists the available backends.

Status matrix:

+---------------+---------+---------+----------+----------+-------+------+---------+
| feature       | mcs6500 | arm     | avr      | msp430   | riscv | stm8 | x86_64  |
+===============+=========+=========+==========+==========+=======+======+=========+
| processor     |         | von     | modified | von      |       |      | von     |
| architecture  |         | Neumann | Harvard  | Neumann  |       |      | Neumann |
+---------------+---------+---------+----------+----------+-------+------+---------+
| native        |         | 32      | 8        | 16       |       |      | 64      |
| bitsize       |         |         |          |          |       |      |         |
+---------------+---------+---------+----------+----------+-------+------+---------+
| Assembly      |         | yes     | yes      | yes      | yes   | yes  | yes     |
| instructions  |         |         |          |          |       |      |         |
|               |         |         |          |          |       |      |         |
+---------------+---------+---------+----------+----------+-------+------+---------+
| Samples       |         | yes     | yes      | yes      | yes   |      | yes     |
| build         |         |         |          |          |       |      |         |
+---------------+---------+---------+----------+----------+-------+------+---------+
| Samples       |         | yes     |          | yes      |       |      | yes     |
| run           |         |         |          |          |       |      |         |
+---------------+---------+---------+----------+----------+-------+------+---------+
| gdb remote    |         |         | yes      |          | yes   |      |         |
| client        |         |         |          |          |       |      |         |
+---------------+---------+---------+----------+----------+-------+------+---------+
| percentage    | 1%      | 70%     | 50%      |   20%    |  70%  |  1%  |   60%   |
| complete      |         |         |          |          |       |      |         |
+---------------+---------+---------+----------+----------+-------+------+---------+


.. _mcs6500:

mcs6500
-------

.. automodule:: ppci.arch.mcs6500

.. _arm:

arm
---

.. automodule:: ppci.arch.arm

.. _avr:

avr
---

.. automodule:: ppci.arch.avr

.. _msp430:

msp430
------

.. automodule:: ppci.arch.msp430

.. _riscv:

risc-v
------

.. automodule:: ppci.arch.riscv

.. _stm8:

stm8
----

.. automodule:: ppci.arch.stm8

.. _x86_64:

x86_64
------

.. automodule:: ppci.arch.x86_64


.. _xtensa:

xtensa
------

.. automodule:: ppci.arch.xtensa

.. include:: backends/xtensa.rst

