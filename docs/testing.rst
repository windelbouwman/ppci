
Compiler testing
================

There are a number of ways to stress test the compiler.

One way is to compile existing C sourcecode, and see if the code compiles and runs.

Current results:

+---------------+----------+---------+
| test sample   | Compiles | Runs    |
+===============+==========+=========+
| libmad        | yes      | ?       |
+---------------+----------+---------+
| 8cc           | yes      | ?       |
+---------------+----------+---------+
| lcc           | no       | ?       |
+---------------+----------+---------+
| micropython   | no       | ?       |
+---------------+----------+---------+

libmad
------

The sourcecode for this test can be found here: https://www.underbit.com/products/mad/

To compile libmad, use the script `tools/compile_libmad.py`. This will compile the libmad sourcecode.

Compilation takes 45 seconds.

8cc
---

8cc is a small C compiler which can compile itself. PPCI can also compile it, running it remains a challenge.

Sourcecode is located here: https://github.com/rui314/8cc

To compile 8cc, use the script `tools/compile_8cc.py`

lcc
---

lcc is a C compiler written in C. Sourcecode can be found here: https://github.com/drh/lcc

To compile this sourcecode, use the script `tools/compile_lcc.py`

micropython
-----------

Micropython is a python implementation for microcontrollers. Website: http://micropython.org/

To compile this sourcecode, use the script `tools/compile_micropython.py`

