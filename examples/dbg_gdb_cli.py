#!/usr/bin/python

import argparse
import logging
from ppci.api import get_arch, get_object
from ppci.binutils.dbg import Debugger
from ppci.binutils.dbg.ptcli import PtDebugCli
from ppci.binutils.dbg.gdb.client import GdbDebugDriver
from ppci.binutils.dbg.gdb.transport import TCP


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('obj', help='Object file to load')
    parser.add_argument(
        '--verbose', '-v', help='Increase verbosity',
        action='count', default=0)
    parser.add_argument('--port', help='gdb port', type=int, default=1234)
    args = parser.parse_args()
    # if args.verbose > 0:
    #    logging.basicConfig(level=logging.DEBUG)
    # else:
    #    logging.basicConfig(level=logging.WARNING)

    obj = get_object(args.obj)
    arch = get_arch(obj.arch)
    transport = TCP(args.port)
    driver = GdbDebugDriver(arch, transport=transport)
    debugger = Debugger(arch, driver)
    debugger.load_symbols(obj, validate=False)
    tui = PtDebugCli(debugger)
    driver.connect()
    try:
        tui.cmdloop()
    finally:
        driver.disconnect()
