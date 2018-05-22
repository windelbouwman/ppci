#!/usr/bin/python

import logging
import time

from ppci.api import get_arch, get_object
from ppci.binutils.dbg import Debugger
from ppci.binutils.dbg.debug_driver import DebugState
from ppci.binutils.dbg.cli import DebugCli
from ppci.binutils.dbg.gdb.client import GdbDebugDriver
from ppci.binutils.dbg.gdb.transport import TCP


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING,format='%(asctime)s (%(threadName)-2s) %(message)s')
    arch = get_arch("riscv")
    transport = TCP(4567)
    time.sleep(1)
    debug_driver = GdbDebugDriver(
        arch, transport=transport, pcresval=0,
        swbrkpt=True)
    debugger = Debugger(arch, debug_driver)
    debug_driver.connect()
    obj = get_object("firmware.oj")
    time.sleep(3)
    debugger.load_symbols(obj, validate=False)
    try:
        DebugCli(debugger,showsource=True).cmdloop()
    finally:        
        debug_driver.disconnect()
