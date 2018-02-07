#!/usr/bin/python

"""
See for a good intro into debuggers:

http://eli.thegreenplace.net/2011/01/23/how-debuggers-work-part-1
http://eli.thegreenplace.net/2011/01/27/how-debuggers-work-part-2-breakpoints

Or take a look at:
http://python-ptrace.readthedocs.org/en/latest/

"""

import os
import ctypes
from ppci.binutils.dbg.debug_driver import DebugDriver, DebugState
from ppci.arch.x86_64 import registers as x86_registers

libc = ctypes.CDLL('libc.so.6')
PTRACE_TRACEME = 0
PTRACE_PEEKTEXT = 1
PTRACE_PEEKDATA = 2
PTRACE_POKETEXT = 4
PTRACE_POKEDATA = 5
PTRACE_CONT = 7
PTRACE_SINGLESTEP = 9
PTRACE_GETREGS = 12
PTRACE_SETREGS = 13

# TODO: what is this calling convention??
libc.ptrace.restype = ctypes.c_ulong
libc.ptrace.argtypes = (
    ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p)


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


class Linux64DebugDriver(DebugDriver):
    """ Implements a debugger backend """
    def __init__(self):
        super().__init__()
        self.pid = None
        self.status = DebugState.STOPPED
        self.breakpoint_backup = {}

    def go_for_it(self, argz):
        self.pid = fork_spawn_stop(argz)
        self.status = DebugState.STOPPED

    # Api:
    def get_status(self):
        return self.status

    @stopped
    def run(self):
        rip = self.get_pc()
        if rip in self.breakpoint_backup:
            # We are at a breakpoint, step over it first!
            self.step_over_bp()

        libc.ptrace(PTRACE_CONT, self.pid, 0, 0)
        self.events.on_start()
        self.status = DebugState.RUNNING

        # TODO: for now, block here??
        print('running')
        _, status = os.wait()

        self.status = DebugState.STOPPED

        print('stopped at breakpoint!')
        rip = self.get_pc()
        self.dec_pc()
        print(self.read_mem(rip - 1, 3))
        self.events.on_stop()

    def dec_pc(self):
        """ Decrease pc by 1 """
        regs = self.get_registers([x86_registers.rip])
        regs[x86_registers.rip] -= 1
        self.set_registers(regs)

    def step_over_bp(self):
        """ Step over a 0xcc breakpoint """
        rip = self.get_pc()
        cc = self.read_mem(rip, 1)
        old_code = self.breakpoint_backup[rip]
        self.write_mem(rip, old_code)
        self.step()
        self.write_mem(rip, cc)

    @stopped
    def step(self):
        self.events.on_start()
        self.status = DebugState.RUNNING
        libc.ptrace(PTRACE_SINGLESTEP, self.pid, 0, 0)
        _, status = os.wait()
        self.status = DebugState.STOPPED
        if not wifstopped(status):
            self.pid = None
        self.events.on_stop()

    @running
    def stop(self):
        print("TODO!")

        # raise NotImplementedError()

    def set_breakpoint(self, address):
        new_code = bytes([0xcc])
        old_code = self.read_mem(address, 1)
        self.write_mem(address, new_code)
        if address not in self.breakpoint_backup:
            self.breakpoint_backup[address] = old_code

    def clear_breakpoint(self, address):
        old_code = self.breakpoint_backup[address]
        self.write_mem(address, old_code)

    # Registers
    @stopped
    def get_registers(self, registers):
        assert self.status == DebugState.STOPPED
        regs = UserRegsStruct()
        libc.ptrace(PTRACE_GETREGS, self.pid, 0, ctypes.byref(regs))
        res = {}
        for register in registers:
            if hasattr(regs, register.name):
                res[register] = getattr(regs, register.name)
        return res

    def set_registers(self, new_regs):
        regs = UserRegsStruct()
        libc.ptrace(PTRACE_GETREGS, self.pid, 0, ctypes.byref(regs))
        for reg_name, reg_value in new_regs.items():
            if hasattr(regs, reg_name):
                setattr(regs, reg_name, reg_value)
        libc.ptrace(PTRACE_SETREGS, self.pid, 0, ctypes.byref(regs))

    # memory:
    def read_mem(self, address, size):
        res = bytearray()
        for offset in range(size):
            res.append(self.read_byte(address + offset))
        return bytes(res)

    def write_mem(self, address, data):
        for offset, b in enumerate(data):
            self.write_byte(address + offset, b)

    def read_byte(self, address):
        """ Convenience wrapper """
        w = self.read_word(address)
        byte = w & 0xff
        return byte

    def write_byte(self, address, byte):
        """ Convenience function to write a single byte """
        w = self.read_word(address)
        w = (w & 0xffffffffffffff00) | byte
        self.write_word(address, w)

    def read_word(self, address):
        res = libc.ptrace(PTRACE_PEEKDATA, self.pid, address, 0)
        return res

    def write_word(self, address, w):
        res = libc.ptrace(PTRACE_POKEDATA, self.pid, address, w)
        assert res != -1

    # Disasm:
    def get_pc(self):
        v = self.get_registers([x86_registers.rip])
        return v[x86_registers.rip]

    def get_fp(self):
        v = self.get_registers([x86_registers.rbp])
        return v[x86_registers.rbp]


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
