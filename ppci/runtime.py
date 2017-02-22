
""" Module with all kind of nice runtimes for various platforms! """

import io
from .binutils.objectfile import ObjectFile
from . import ir


def make_trampoline(func_name):
    """ Create a main function that calls another function """
    mod = ir.Module('main')
    main = ir.Procedure('main')
    mod.add_function(main)
    entry = ir.Block('entry')
    main.add_block(entry)
    main.entry = entry
    entry.add_instruction(ir.ProcedureCall(func_name, []))
    entry.add_instruction(ir.Exit())
    return mod


def create_linux_exe(function_name: str, name, obj: ObjectFile):
    """ Create an executable for the given system """
    from .api import c3c, asm, link, objcopy, ir_to_object

    march = obj.arch

    obj1 = c3c([io.StringIO(RT_IO_C3), io.StringIO(LINUX_BSP)], [], march)
    obj2 = asm(io.StringIO(LINUX_CRT0), march)
    trampoline = make_trampoline(function_name)
    obj3 = ir_to_object([trampoline], march)
    obj = link([obj, obj1, obj2, obj3], layout=io.StringIO(LINUX_MMAP))
    objcopy(obj, None, 'elf', name)
    print(obj)


# TODO: is this really a runtime?

RT_IO_C3 = """
module io;
import bsp;

public function void println(string txt)
{
    print(txt);
    bsp.putc(10); // Newline!
}

public function void print(string txt)
{
    var int i;
    i = 0;

    while (i < txt->len)
    {
        bsp.putc(txt->txt[i]);
        i = i + 1;
    }
}
"""


LINUX_BSP = """
module bsp;

public function void putc(byte c)
{
  syscall(1, 1, cast<int>(&c), 1);
}

function void exit()
{
    syscall(60, 0, 0, 0);
}

function void syscall(int nr, int a, int b, int c);

"""

LINUX_CRT0 = """
section reset

start:
    call main_main
    call bsp_exit

bsp_syscall:
    mov rax, rdi ; abi param 1
    mov rdi, rsi ; abi param 2
    mov rsi, rdx ; abi param 3
    mov rdx, rcx ; abi param 4
    syscall
    ret
"""

LINUX_MMAP = """
MEMORY code LOCATION=0x40000 SIZE=0x10000 {
    SECTION(reset)
    ALIGN(4)
    SECTION(code)
}

MEMORY ram LOCATION=0x20000000 SIZE=0xA000 {
    SECTION(data)
}
"""
