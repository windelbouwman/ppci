
Debugging
=========

Debugging tests
~~~~~~~~~~~~~~~

To debug test cases, a handy trick is to use pudb (when not using fancy ide
like vscode or pycharm). To do this, specify the debugger to use with pytest
like this:

.. code:: bash

    $ pytest -v --pdb --pdbcls pudb.debugger:Debugger --capture=no

Debugging dynamic code
~~~~~~~~~~~~~~~~~~~~~~

Sometimes, the python interpreter might crash due to playing with dynamically
injected code. To debug this, we can use gdb for example.

.. code:: bash

    $ gdb --args python script.py
    (gdb) run

Once the program crashes, one can disassemble and print info:

.. code:: bash

    (gdb) bt
    (gdb) disassemble /r 0x7fff000, 0x7fff200
    (gdb) info registers

Debugging python code
~~~~~~~~~~~~~~~~~~~~~

Alternatively, when facing a python exception, one might want to try the pudb
debugger like this:

.. code:: bash

    $ python -m pudb crashing_script.py

Debugging sample snippets
~~~~~~~~~~~~~~~~~~~~~~~~~

The folder ``test/samples`` contains sample snippets of
code with corresponding output. Those samples are compiled
and run during testing. If one of those samples fails,
troubleshooting begins.

There are several approaches to pinpoint the issue:

- Examination of the compilation report. Each test case
  generates a HTML report with detailed information about
  the compilation steps. This can be handy to determine
  where the process generated wrong code.

- Run the sample binary with QEMU. This involves stepping
  through the generated binary and keeping an eye on register
  and memory values.

Debugging with QEMU
~~~~~~~~~~~~~~~~~~~

Qemu has a mode in which it will dump very detailed information
about each instruction executed.

Use the following line to get a whole lot of info:

.. code:: bash

    $ qemu-system-or1k -D trace.txt -d in_asm,exec,int,op_opt,cpu -singlestep

Note the -singlestep option here will execute every single instruction at a time.

This can produce helpful instruction tracing like this:


.. code::

    ----------------
    IN: 
    0x00000100:  l.j       2

    OP after optimization and liveness analysis:
    ld_i32 tmp0,env,$0xfffffffffffffff0      dead: 1  pref=0xffff
    movi_i32 tmp1,$0x0                       pref=0xffff
    brcond_i32 tmp0,tmp1,lt,$L0              dead: 0 1

    ---- 00000100 00000000                
    movi_i32 jmp_pc,$0x108                   sync: 0  dead: 0  pref=0xffff
    movi_i32 dflag,$0x1                      sync: 0  dead: 0  pref=0xffff
    movi_i32 ppc,$0x100                      sync: 0  dead: 0  pref=0xffff
    goto_tb $0x0                           
    movi_i32 pc,$0x104                       sync: 0  dead: 0  pref=0xffff
    exit_tb $0x7fc8a8300040                
    set_label $L0                          
    exit_tb $0x7fc8a8300043                

    Trace 0: 0x7fc8a8300100 [00000000/00000100/0x5] 
    PC=00000100
    R00=00000000 R01=00000000 R02=00000000 R03=00000000
    R04=00000000 R05=00000000 R06=00000000 R07=00000000
    R08=00000000 R09=00000000 R10=00000000 R11=00000000
    R12=00000000 R13=00000000 R14=00000000 R15=00000000
    R16=00000000 R17=00000000 R18=00000000 R19=00000000
    R20=00000000 R21=00000000 R22=00000000 R23=00000000
    R24=00000000 R25=00000000 R26=00000000 R27=00000000
    R28=00000000 R29=00000000 R30=00000000 R31=00000000
    ----------------
    IN: 
    0x00000104:  l.nop     

    OP after optimization and liveness analysis:
    ld_i32 tmp0,env,$0xfffffffffffffff0      dead: 1  pref=0xffff
    movi_i32 tmp1,$0x0                       pref=0xffff
    brcond_i32 tmp0,tmp1,lt,$L0              dead: 0 1

    ---- 00000104 00000001                
    movi_i32 dflag,$0x0                      sync: 0  dead: 0  pref=0xffff
    movi_i32 ppc,$0x104                      sync: 0  dead: 0  pref=0xffff
    mov_i32 pc,jmp_pc                        sync: 0  dead: 0 1  pref=0xffff
    discard jmp_pc                           pref=none
    call lookup_tb_ptr,$0x6,$1,tmp2,env      dead: 1  pref=none
    goto_ptr tmp2                            dead: 0
    set_label $L0                          
    exit_tb $0x7fc8a8300183                

    Linking TBs 0x7fc8a8300100 [00000100] index 0 -> 0x7fc8a8300240 [00000104]
    Trace 0: 0x7fc8a8300240 [00000000/00000104/0x7] 
    PC=00000104
    R00=00000000 R01=00000000 R02=00000000 R03=00000000
    R04=00000000 R05=00000000 R06=00000000 R07=00000000
    R08=00000000 R09=00000000 R10=00000000 R11=00000000
    R12=00000000 R13=00000000 R14=00000000 R15=00000000
    R16=00000000 R17=00000000 R18=00000000 R19=00000000
    R20=00000000 R21=00000000 R22=00000000 R23=00000000
    R24=00000000 R25=00000000 R26=00000000 R27=00000000
    R28=00000000 R29=00000000 R30=00000000 R31=00000000
    ----------------

