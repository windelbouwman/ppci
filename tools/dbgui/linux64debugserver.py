#!/usr/bin/python

"""
See for a good intro into debuggers:

http://eli.thegreenplace.net/2011/01/23/how-debuggers-work-part-1

Or take a look at:
http://python-ptrace.readthedocs.org/en/latest/

Usage example:
./linux64debugserver.py ../../test/listings/testsamplesTestSamplesOnX86Linuxtestswmul.elf

"""

import os
import sys
import ctypes
import struct
from ppci.dbg import DebugServer, RUNNING, STOPPED

libc = ctypes.CDLL('libc.so.6')
PTRACE_TRACEME = 0
PTRACE_PEEKTEXT = 1
PTRACE_PEEKDATA = 2
PTRACE_CONT = 7
PTRACE_SINGLESTEP = 9
PTRACE_GETREGS = 12


class UserRegsStruct(ctypes.Structure):
    _fields_ = [
        ("r15", ctypes.c_ulonglong),
        ("r14", ctypes.c_ulonglong),
        ("r13", ctypes.c_ulonglong),
        ("r12", ctypes.c_ulonglong),
        ("rbp", ctypes.c_ulonglong),
        ("rbx", ctypes.c_ulonglong),
        ("r11", ctypes.c_ulonglong),
        ("r10", ctypes.c_ulonglong),
        ("r9", ctypes.c_ulonglong),
        ("r8", ctypes.c_ulonglong),
        ("rax", ctypes.c_ulonglong),
        ("rcx", ctypes.c_ulonglong),
        ("rdx", ctypes.c_ulonglong),
        ("rsi", ctypes.c_ulonglong),
        ("rdi", ctypes.c_ulonglong),
        ("orig_rax", ctypes.c_ulonglong),
        ("rip", ctypes.c_ulonglong),
        ("cs", ctypes.c_ulonglong),
        ("eflags", ctypes.c_ulonglong),
        ("rsp", ctypes.c_ulonglong),
        ("ss", ctypes.c_ulonglong),
        ("fs_base", ctypes.c_ulonglong),
        ("gs_base", ctypes.c_ulonglong),
        ("ds", ctypes.c_ulonglong),
        ("es", ctypes.c_ulonglong),
        ("fs", ctypes.c_ulonglong),
        ("gs", ctypes.c_ulonglong),
    ]


# Idea: use decorators to assert state?
def stopped(f):
    def f2():
        pass
    return f


def running(f):
    return f


class LinuxDebugServer(DebugServer):
    """ Implements a debugger backend """
    def __init__(self):
        super().__init__()
        self.pid = None
        self.status = STOPPED

    def go_for_it(self, argz):
        self.pid = fork_spawn_stop(argz)
        self.status = STOPPED

    # Api:
    def get_status(self):
        return self.status

    @stopped
    def run(self):
        libc.ptrace(PTRACE_CONT, self.pid, 0, 0)
        self.status = RUNNING

    @stopped
    def step(self):
        self.status = RUNNING
        libc.ptrace(PTRACE_SINGLESTEP, self.pid, 0, 0)
        _, status = os.wait()
        self.status = STOPPED
        if not wifstopped(status):
            self.pid = None

    @running
    def stop(self):
        print("TODO!")

        #raise NotImplementedError()

    # Registers
    @stopped
    def get_registers(self, register_names):
        assert self.status == STOPPED
        regs = UserRegsStruct()
        libc.ptrace(PTRACE_GETREGS, self.pid, 0, ctypes.byref(regs))
        res = {}
        for reg_name in register_names:
            if hasattr(regs, reg_name):
                res[reg_name] = getattr(regs, reg_name)
        return res

    # memory:
    def read_mem(self, address, size):
        res = bytearray()
        a2 = address + size
        while address < a2:
            part = self.read_word(address)
            address += len(part)
            res.extend(part)
        return bytes(res)

    def read_word(self, address):
        res = libc.ptrace(PTRACE_PEEKDATA, self.pid, address, 0)
        print(address, res)
        return struct.pack('<i', res)

    # Disasm:
    def get_pc(self):
        v = self.get_registers(['rip'])
        return v['rip']


def wifstopped(status):
    return (status & 0xff) == 0x7f


def fork_spawn_stop(argz):
    """ Spawn new process and stop it on first instruction """
    pid = os.fork()
    if pid == 0:  # Child process
        # Allow the child process to be ptraced
        libc.ptrace(PTRACE_TRACEME, 0, 0, 0)

        # Launch the intended program:
        os.execv(argz[0], argz)

        # This point will never be reached!
        assert False
    else:
        _, status = os.wait()
        return pid


if __name__ == '__main__':
    server = LinuxDebugServer()
    server.go_for_it(sys.argv[1:])
    server.serve()
