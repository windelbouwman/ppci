

.. _or1k:

Open risc
---------

Qemu
~~~~

When booting with qemu, the loading of a raw binary goes wrong as of qemu
version 2.11. Instead of loading a raw binary, an uboot image can be created
with :func:`ppci.utils.uboot_image.write_uboot_image`.

.. code:: bash

   $ qemu-system-or1k -kernel baremetal.uimage -M or1k-sim -serial stdio -m 16M

The memory is mapped as follows:

.. code::

    (qemu) info mtree
    address-space: memory
      0000000000000000-ffffffffffffffff (prio 0, i/o): system
        0000000000000000-0000000000ffffff (prio 0, ram): openrisc.ram
        0000000090000000-0000000090000007 (prio 0, i/o): serial
        0000000092000000-0000000092000053 (prio 0, i/o): open_eth.regs
        0000000092000400-00000000920007ff (prio 0, i/o): open_eth.desc

    address-space: I/O
      0000000000000000-000000000000ffff (prio 0, i/o): io

    address-space: cpu-memory
      0000000000000000-ffffffffffffffff (prio 0, i/o): system
        0000000000000000-0000000000ffffff (prio 0, ram): openrisc.ram
        0000000090000000-0000000090000007 (prio 0, i/o): serial
        0000000092000000-0000000092000053 (prio 0, i/o): open_eth.regs
        0000000092000400-00000000920007ff (prio 0, i/o): open_eth.desc


To get a lot of debug output, the trace option of qemu can be used:

.. code::

    -D trace.txt -d in_asm,exec,int,op_opt,cpu


Module
~~~~~~

.. automodule:: ppci.arch.or1k
    :members:

