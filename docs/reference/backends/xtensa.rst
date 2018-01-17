
.. _xtensa:

xtensa
------

Module
~~~~~~

.. automodule:: ppci.arch.xtensa
    :members:

Testing
~~~~~~~

The xtensa backend

You can run xtensa with qemu:

.. code:: bash

    $ qemu-system-xtensa -M lx60 -m 96M -pflash lx60.flash -serial stdio


This will run the lx60 emulated board. This is an Avnet board with an fpga
and an emulated xtensa core on it. This board can boot from parallel flash
(pflash).

The memory is mapped as follows, you can see it in the qemu monitor with
the 'info mtree' command:

.. code::

    (qemu) info mtree
    address-space: memory
      0000000000000000-ffffffffffffffff (prio 0, RW): system
        0000000000000000-0000000005ffffff (prio 0, RW): lx60.dram
        00000000f0000000-00000000fdffffff (prio 0, RW): lx60.io
          00000000f8000000-00000000f83fffff (prio 0, R-): lx60.io.flash
          00000000fd020000-00000000fd02ffff (prio 0, RW): lx60.fpga
          00000000fd030000-00000000fd030053 (prio 0, RW): open_eth.regs
          00000000fd030400-00000000fd0307ff (prio 0, RW): open_eth.desc
          00000000fd050020-00000000fd05003f (prio 0, RW): serial
          00000000fd800000-00000000fd803fff (prio 0, RW): open_eth.ram
        00000000fe000000-00000000fe3fffff (prio 0, RW): alias lx60.flash @lx60.io.flash 0000000000000000-00000000003fffff

    address-space: I/O
      0000000000000000-000000000000ffff (prio 0, RW): io

    address-space: cpu-memory
      0000000000000000-ffffffffffffffff (prio 0, RW): system
        0000000000000000-0000000005ffffff (prio 0, RW): lx60.dram
        00000000f0000000-00000000fdffffff (prio 0, RW): lx60.io
          00000000f8000000-00000000f83fffff (prio 0, R-): lx60.io.flash
          00000000fd020000-00000000fd02ffff (prio 0, RW): lx60.fpga
          00000000fd030000-00000000fd030053 (prio 0, RW): open_eth.regs
          00000000fd030400-00000000fd0307ff (prio 0, RW): open_eth.desc
          00000000fd050020-00000000fd05003f (prio 0, RW): serial
          00000000fd800000-00000000fd803fff (prio 0, RW): open_eth.ram
        00000000fe000000-00000000fe3fffff (prio 0, RW): alias lx60.flash @lx60.io.flash 0000000000000000-00000000003fffff

    memory-region: lx60.io.flash
      0000000008000000-00000000083fffff (prio 0, R-): lx60.io.flash


The lx60 emulation has also an mmu, which means it uses a memory translation
unit. Therefore, the RAM is mapped from 0xd8000000 to 0x00000000.


A working memory map for this target is:

.. code::

    MEMORY flash LOCATION=0xfe000000 SIZE=0x10000 {
        SECTION(reset)
        ALIGN(4)
        SECTION(code)
    }

    MEMORY ram LOCATION=0xd8000000 SIZE=0x10000 {
        SECTION(data)
    }

Code starts to run from the first byte of the flash image, and is mapped
at 0xfe000000.

