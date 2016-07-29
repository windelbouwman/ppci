import argparse
import logging
from ppci.api import get_arch
from ppci.binutils.dbg import Debugger
from ppci.binutils.dbg_cli import DebugCli
from ppci.binutils.dbg_gdb_client import GdbDebugDriver


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('arch')
    parser.add_argument('obj')
    args = parser.parse_args()
    arch = get_arch(args.arch)
    debugger = Debugger(arch, GdbDebugDriver(arch, port=1234))
    debugger.load_symbols(args.obj, validate=False)
    DebugCli(debugger).cmdloop()
