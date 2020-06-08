
Changelog
=========

Release 1.0 (Planned)
---------------------

* platform.python_compiler() returns 'ppci 1.0'

Release 0.5.9 (Upcoming)
------------------------

Release 0.5.8 (Jun 8, 2020)
---------------------------

* Add inline asm support to C frontend.
* Work on pascal frontend
* Add initial support for relocatable ELF file
* Add initial command to run wasm files directly
* CoreMark benchmark can be compiled and run

Release 0.5.7 (Dec 31, 2019)
----------------------------

* Added support for the m68k processor.
* Added support for the microblaze processor.
* Added RISCV floating point support (by Michael).
* Add S-record format.
* Add amiga hunk format.
* Add OCaml bytecode file reader.
* Use black formatter

Release 0.5.6 (Aug 22, 2018)
----------------------------

* Compilation is now reproducible: recompiling the same source yields exactly the same machine code
* Added support for webassembly WAT file format (by Almar)
* Improved compilation speed
* Separation of the graph algorithms in ppci.graph.

Release 0.5.5 (Jan 17, 2018)
----------------------------

* Addition of WASM support (by Almar)
* Added compilation of subset of python
* Changed commandline tools from scripts into setuptools entrypoints
* Add support for function pointers in C
* Add uboot legacy image utility
* Start of exe support
* Start of mips support

Release 0.5.4 (Aug 26, 2017)
----------------------------

* Addition of open risc (or1k) architecture support
* Added command line options to emit assembly output
* Created ppci.lang.tools module with helper classes for parsing and lexing

Release 0.5.3 (Apr 27, 2017)
----------------------------

* Initial version of C preprocessor
* Improved calling convention handling
* Initial version of pascal front-end

Release 0.5.2 (Dec 29, 2016)
----------------------------

* Better floating point support in c3
* Addition of the xtensa target architecture
* Extended the supported 6502 instructions

Release 0.5.1 (Oct 16, 2016)
----------------------------

* Expand the riscv example to include single stepping (by Michael)
* Bugfix in byte parameter passing for x86_64 target
* Cleanup of the encoding system
* Start with llvm-IR frontend


Release 0.5 (Aug 6, 2016)
-------------------------

* Debug type information stored in better format
* Expression evaluation in debugger
* Global variables can be viewed
* Improved support for different register classes

Release 0.4.0 (Apr 27, 2016)
----------------------------

* Start with debugger and disassembler


Release 0.3.0 (Feb 23, 2016)
----------------------------

* Added risc v architecture
* Moved thumb into arm arch
* msp430 improvements

Release 0.2.0 (Jan 23, 2016)
----------------------------

* Added linker (ppci-ld.py) command
* Rename `buildfunctions` to `api`
* Rename `target` to `arch`

Release 0.1.0 (Dec 29, 2015)
----------------------------

* Added x86_64 target.
* Added msp430 target.

Release 0.0.5 (Mar 21, 2015)
----------------------------

* Remove st-link and hence pyusb dependency.
* Support for pypy3.

Release 0.0.4 (Feb 24, 2015)
----------------------------

Release 0.0.3 (Feb 17, 2015)
----------------------------

Release 0.0.2 (Nov 9, 2014)
---------------------------

Release 0.0.1 (Oct 10, 2014)
----------------------------

* Initial release.
