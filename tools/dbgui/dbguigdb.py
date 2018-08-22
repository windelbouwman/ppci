#!/usr/bin/python

import sys
import argparse
import logging
from ppci import api
from ppci.common import logformat
from ppci.binutils.dbg import Debugger
from ppci.binutils.dbg.gdb.client import GdbDebugDriver
from ppci.binutils.dbg.gdb.transport import TCP
from dbgui import DebugUi, QtWidgets


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'obj', help='The object file with the debug information')
    parser.add_argument('--port', help='gdb port', type=int, default=1234)
    args = parser.parse_args()

    logging.basicConfig(format=logformat, level=logging.DEBUG)
    app = QtWidgets.QApplication(sys.argv)

    obj = api.get_object(args.obj)
    arch = api.get_arch(obj.arch)
    transport = TCP(args.port)
    debug_driver = GdbDebugDriver(arch, transport=transport)
    debug_driver.connect()
    debugger = Debugger(arch, debug_driver)
    debugger.load_symbols(obj, validate=False)

    ui = DebugUi(debugger)
    ui.memview.address = obj.get_image('ram').address
    ui.open_all_source_files()
    ui.show()
    try:
        app.exec_()
    finally:
        debugger.shutdown()
        debug_driver.disconnect()
