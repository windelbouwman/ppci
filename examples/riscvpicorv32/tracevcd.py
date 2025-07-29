import sys, os, string
import binascii
import struct
from sys import argv
from vcd import parse_vcd
from types import SimpleNamespace as New
from ppci.api import get_arch, get_object
from ppci.binutils.dbg import Debugger
from ppci.binutils.dbg.debug_driver import DebugState
from ppci.binutils.dbg.cli import DebugCli
from ppci.binutils.dbg.gdb.client import GdbDebugDriver
from ppci.binutils.dbg.gdb.transport import TCP
from ppci.binutils.debuginfo import (
    DebugPointerType,
    DebugAddress,
    FpOffsetAddress,
    DebugBaseType,
)


def calc_address(obj, address):
    """Calculate the actual address based on section and offset"""
    if isinstance(address, DebugAddress):
        section = obj.get_section(address.section)
        return section.address + address.offset
    else:  # pragma: no cover
        raise NotImplementedError(str(address))


def getfunc(obj, adr):
    """Determine the function to"""
    for function in obj.debug_info.functions:
        begin = calc_address(obj, function.begin)
        end = calc_address(obj, function.end)
        if adr in range(begin, end):
            return function


def getsigvalstr(name, argtype=None):
    global signals
    typemap = {
        "int": "{0:d}",
        "char": "{0:c}",
        "uint": "{0:08x}",
        "void": "{0:08x}",
    }
    signal = signals[name]
    curvalstr = signal.timevals[signal.timeslot][1]
    if isinstance(argtype, DebugBaseType):
        typename = argtype.name
    else:
        typename = "uint"
    if curvalstr != "x":
        type = typemap[typename]
        curvalstr = type.format(int(curvalstr, 2))
    return curvalstr


if __name__ == "__main__":
    # --- load debug information
    arch = get_arch("riscv")
    transport = TCP(4567)
    debug_driver = GdbDebugDriver(
        arch, transport=transport, pcresval=0, swbrkpt=True
    )
    debugger = Debugger(arch, debug_driver)
    obj = get_object("firmware.oj")
    debugger.load_symbols(obj, validate=False)
    table = parse_vcd(
        "./verilator/picorv32.vcd",
        [
            "TOP.CLK",
            "TOP.SYSTEM.PICORV32_CORE.REG_PC[31:0]",
            "TOP.SYSTEM.PICORV32_CORE.DBG_REG_X10[31:0]",
            "TOP.SYSTEM.PICORV32_CORE.DBG_REG_X12[31:0]",
            "TOP.SYSTEM.PICORV32_CORE.DBG_REG_X13[31:0]",
            "TOP.SYSTEM.PICORV32_CORE.DBG_REG_X14[31:0]",
            "TOP.SYSTEM.PICORV32_CORE.DBG_REG_X15[31:0]",
            "TOP.SYSTEM.PICORV32_CORE.DBG_REG_X16[31:0]",
            "TOP.SYSTEM.PICORV32_CORE.DBG_REG_X17[31:0]",
            "TOP.SYSTEM.PICORV32_CORE.MEM_ADDR[31:0]",
            "TOP.SYSTEM.PICORV32_CORE.MEM_RDATA[31:0]",
            "TOP.SYSTEM.PICORV32_CORE.MEM_WDATA[31:0]",
            "TOP.SYSTEM.PICORV32_CORE.MEM_WSTRB[3:0]",
            "TOP.SYSTEM.PICORV32_CORE.MEM_VALID",
            "TOP.SYSTEM.PICORV32_CORE.MEM_READY",
        ],
        "us",
    )
    codes = list(table.keys())
    globals = []
    global signals
    signals = {}
    pctimevals = []
    for code in table.keys():
        name = table[code]["nets"][0]["name"]
        tv = table[code]["tv"]
        if name == "CLK":
            clktimevals = tv
        else:
            signals[name] = New(timeslot=0, change=False, timevals=tv)

    argregs = [
        "DBG_REG_X12[31:0]",
        "DBG_REG_X13[31:0]",
        "DBG_REG_X14[31:0]",
        "DBG_REG_X15[31:0]",
        "DBG_REG_X16[31:0]",
        "DBG_REG_X17[31:0]",
    ]
    returnreg = "DBG_REG_X10[31:0]"
    pcreg = "REG_PC[31:0]"
    mem_addr = "MEM_ADDR[31:0]"
    mem_valid = "MEM_VALID"
    mem_ready = "MEM_READY"
    mem_wstrb = "MEM_WSTRB[3:0]"
    mem_rdata = "MEM_RDATA[31:0]"
    mem_wdata = "MEM_WDATA[31:0]"
    calledfunc = ""
    pcval = 0
    newfunc = getfunc(obj, pcval)
    callstack = []
    callstack.append("startup")
    oldfunc = None
    newfunc = None
    globals = []
    watchadr = {}
    for var in globals:
        watchadr[obj.get_symbol_value(var)] = var
    for time, clkvalstr in clktimevals:
        clkval = int(clkvalstr, 2)
        if clkval:
            for name, signal in signals.items():
                signal.change = False
                while (
                    len(signal.timevals) - 1 > signal.timeslot
                    and signal.timevals[signal.timeslot + 1][0] < time
                ):
                    signal.timeslot += 1
                    signal.change = True

            lastpcval = pcval
            pcvalstr = getsigvalstr(pcreg)
            pcval = int(pcvalstr, 16)

            if pcval != lastpcval:
                if newfunc:
                    oldfunc = newfunc
                newfunc = getfunc(obj, pcval)
                if newfunc != oldfunc:
                    if newfunc and newfunc.name == callstack[-1]:
                        curvalstr = getsigvalstr(
                            returnreg, oldfunc.return_type
                        )
                        print(
                            "@time=%d us, funktion %s returned:"
                            % (time, oldfunc.name)
                        )
                        print(
                            "Returnvalue(%s):%s"
                            % (oldfunc.return_type, curvalstr)
                        )
                        callstack.pop()
                    elif newfunc:
                        print(
                            "@time=%d us, PC=%08x funktion %s(%08x) called:"
                            % (time, lastpcval, newfunc.name, pcval)
                        )
                        for argnr, arg in enumerate(newfunc.arguments):
                            curvalstr = getsigvalstr(argregs[argnr], arg.typ)
                            print(
                                "Args:%s(%s) = %s"
                                % (arg.name, arg.typ, curvalstr)
                            )
                        if oldfunc:
                            callstack.append(oldfunc.name)

            curvalstr = getsigvalstr(mem_addr)
            if curvalstr != "x":
                memadr = int(curvalstr, 16)
            else:
                memadr = 0
            if memadr in watchadr.keys():
                curvalstr = getsigvalstr(mem_valid)
                valid = int(curvalstr, 16)
                curvalstr = getsigvalstr(mem_ready)
                ready = int(curvalstr, 16)
                curvalstr = getsigvalstr(mem_wstrb)
                wstrobe = int(curvalstr, 16)
                if valid and not wstrobe and ready:
                    var = watchadr[memadr]
                    curvalstr = getsigvalstr(mem_rdata)
                    print(
                        "@time=%d us, read var %s data:%s"
                        % (time, var, curvalstr)
                    )

                if valid and wstrobe and ready:
                    var = watchadr[memadr]
                    curvalstr = getsigvalstr(mem_wdata)
                    print(
                        "@time=%d us, write var %s with data:%s"
                        % (time, var, curvalstr)
                    )
