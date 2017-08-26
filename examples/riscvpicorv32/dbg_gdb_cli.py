#!/usr/bin/python

import time
import argparse
import logging
from ppci.api import get_arch, get_object
from ppci.binutils.dbg import Debugger, STOPPED, RUNNING
from ppci.binutils.dbg_cli import DebugCli
from ppci.binutils.dbg_gdb_client import GdbDebugDriver
from ppci.binutils.transport import TCP

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    arch = get_arch("riscv")
    transport = TCP(4567)
    time.sleep(1)
    debugger = Debugger(arch, GdbDebugDriver(arch, transport=transport, constat=RUNNING, pcresval=0, swbrkpt=True))
    obj = get_object("firmware.tlf")
    debugger.load_symbols(obj, validate=False)
    DebugCli(debugger, showsource=True).cmdloop()
