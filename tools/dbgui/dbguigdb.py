#!/usr/bin/python

import sys
import argparse
import ppci.common
import logging
from ppci import api
from ppci.binutils.dbg import Debugger
from ppci.binutils.dbg_gdb_client import GdbDebugDriver
from ppci.binutils.transport import TCP
from dbgui import DebugUi, QtWidgets


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'obj', help='The object file with the debug information')
    parser.add_argument('--port', help='gdb port', type=int, default=1234)
    args = parser.parse_args()

    logging.basicConfig(format=ppci.common.logformat, level=logging.DEBUG)
    app = QtWidgets.QApplication(sys.argv)

    obj = api.get_object(args.obj)
    arch = api.get_arch(obj.arch)
    debug_driver = GdbDebugDriver(arch, transport=TCP(args.port))
    debugger = Debugger(arch, debug_driver)
    debugger.load_symbols(obj, validate=False)

    ui = DebugUi(debugger)
    ui.memview.address = obj.get_image('ram').location
    ui.open_all_source_files()
    ui.show()
    app.exec_()
    debugger.shutdown()
