#!/usr/bin/python

import argparse
import logging
from ppci.api import get_arch, get_object
from ppci.binutils.dbg import Debugger, STOPPED, RUNNING
from ppci.binutils.dbg_cli import DebugCli
from ppci.binutils.dbg_gdb_client import GdbDebugDriver



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    arch = get_arch("riscv")
    debugger = Debugger(arch, GdbDebugDriver(arch, port=4567, constat=RUNNING))
    obj = get_object("firmware.tlf")
    debugger.load_symbols(obj, validate=False)
    DebugCli(debugger).cmdloop()
