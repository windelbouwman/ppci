#!/usr/bin/python

import argparse
import logging
from ppci.api import get_arch, get_object
from ppci.binutils.dbg import Debugger
from ppci.binutils.dbg_cli import DebugCli
from ppci.binutils.dbg_gdb_client import GdbDebugDriver
from ppci.binutils.transport import TCP


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('obj', help='Object file to load')
    parser.add_argument(
        '--verbose', '-v', help='Increase verbosity',
        action='count', default=0)
    parser.add_argument('--port', help='gdb port', type=int, default=1234)
    args = parser.parse_args()
    if args.verbose > 0:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    obj = get_object(args.obj)
    arch = get_arch(obj.arch)
    tcp = TCP(args.port)
    debugger = Debugger(arch, GdbDebugDriver(arch, transport=tcp))
    debugger.load_symbols(obj, validate=False)
    DebugCli(debugger).cmdloop()
