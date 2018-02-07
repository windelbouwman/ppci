#!/usr/bin/python

# import logging
import time

from ppci.api import get_arch, get_object
from ppci.binutils.dbg import Debugger
from ppci.binutils.dbg.ptcli import PtDebugCli
from ppci.binutils.dbg.gdb.client import GdbDebugDriver
from ppci.binutils.dbg.gdb.transport import TCP


if __name__ == "__main__":
    # logging.basicConfig(level=logging.WARNING)
    arch = get_arch("riscv")
    transport = TCP(4567)
    debug_driver = GdbDebugDriver(
        arch, transport=transport, pcresval=0, swbrkpt=True)
    debugger = Debugger(arch, debug_driver)
    pt_cli = PtDebugCli(debugger)
    debug_driver.connect()
    # debugger.stop()
    obj = get_object("firmware.oj")
    time.sleep(3)
    debugger.load_symbols(obj, validate=False)
    try:
        pt_cli.cmdloop()
    finally:
        transport.disconnect()
