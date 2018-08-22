

Debug
=====

When an application is build, it often has to be debugged. This section
describes the peculiarities of debugging.

Debugger
--------

The debugger architecture is depicted below:

.. graphviz::

   digraph x {
   dbg_cli [label="Debug Command Line Interface"]
   dbg_qt [label="Qt user interface"]
   dbg_pt [label="Prompt_toolkit user interface"]
   debugger [label="Debugger"]
   dbg_cli -> debugger
   dbg_qt -> debugger
   dbg_pt -> debugger
   debugger -> debug_interface
   debug_interface [label="Debug Driver Interface"]
   debug_interface -> gdb_client
   debug_interface -> dummy_interface
   gdb_client -> transport
   transport -> socket
   transport -> serial
   }

The debugger class is the main piece of the debugger. This is created for
a specific architecture and is given a driver to communicate with the target
hardware.

.. autoclass:: ppci.binutils.dbg.Debugger
    :members: run, step, stop, set_breakpoint, clear_breakpoint,
              read_mem, write_mem

One of the classes that uses the debugger is the debug command line interface.

.. autoclass:: ppci.binutils.dbg.cli.DebugCli
    :members:

To connect to your favorite hardware, subclass the DebugDriver class.

.. autoclass:: ppci.binutils.dbg.DebugDriver
    :members:

The following class can be used to connect to a gdb server:

.. autoclass:: ppci.binutils.dbg.gdb.client.GdbDebugDriver
    :members:


Debug info file formats
-----------------------

Debug information is of a complex nature. Various file formats exist
to store this information. This section gives a short overview of the
different formats.

pdb format
~~~~~~~~~~

This is the microsoft debug format.

https://en.wikipedia.org/wiki/Program_database


Dwarf format
~~~~~~~~~~~~

How a linked list is stored in dwarf format.


.. code::

    struct ll {
      int a;
      struct ll *next;
    };


.. code::

    <1><57>: Abbrev Number: 3 (DW_TAG_base_type)
        <58>   DW_AT_byte_size   : 4
        <59>   DW_AT_encoding    : 5    (signed)
        <5a>   DW_AT_name        : int
     <1><5e>: Abbrev Number: 2 (DW_TAG_base_type)
        <5f>   DW_AT_byte_size   : 8
        <60>   DW_AT_encoding    : 5    (signed)
        <61>   DW_AT_name        : (indirect string, offset: 0x65): long int
     <1><65>: Abbrev Number: 2 (DW_TAG_base_type)
        <66>   DW_AT_byte_size   : 8
        <67>   DW_AT_encoding    : 7    (unsigned)
        <68>   DW_AT_name        : (indirect string, offset: 0xf6): sizetype
     <1><6c>: Abbrev Number: 2 (DW_TAG_base_type)
        <6d>   DW_AT_byte_size   : 1
        <6e>   DW_AT_encoding    : 6    (signed char)
        <6f>   DW_AT_name        : (indirect string, offset: 0x109): char
     <1><73>: Abbrev Number: 4 (DW_TAG_structure_type)
        <74>   DW_AT_name        : ll
        <77>   DW_AT_byte_size   : 16
        <78>   DW_AT_decl_file   : 1
        <79>   DW_AT_decl_line   : 4
        <7a>   DW_AT_sibling     : <0x95>
     <2><7e>: Abbrev Number: 5 (DW_TAG_member)
        <7f>   DW_AT_name        : a
        <81>   DW_AT_decl_file   : 1
        <82>   DW_AT_decl_line   : 5
        <83>   DW_AT_type        : <0x57>
        <87>   DW_AT_data_member_location: 0
     <2><88>: Abbrev Number: 6 (DW_TAG_member)
        <89>   DW_AT_name        : (indirect string, offset: 0xf1): next
        <8d>   DW_AT_decl_file   : 1
        <8e>   DW_AT_decl_line   : 6
        <8f>   DW_AT_type        : <0x95>
        <93>   DW_AT_data_member_location: 8
     <2><94>: Abbrev Number: 0
     <1><95>: Abbrev Number: 7 (DW_TAG_pointer_type)
        <96>   DW_AT_byte_size   : 8
        <97>   DW_AT_type        : <0x73>


