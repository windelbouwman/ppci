#!/usr/bin/python

import sys
import argparse
import ppci.common
import logging
from ppci import api
from ppci.binutils.dbg import Debugger, GdbDebugDriver
from dbgui import DebugUi, QtWidgets


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'obj', help='The object file with the debug information')
    args = parser.parse_args()
    obj = args.obj

    logging.basicConfig(format=ppci.common.logformat, level=logging.DEBUG)
    app = QtWidgets.QApplication(sys.argv)

    debug_driver = GdbDebugDriver()
    debugger = Debugger(api.get_arch('riscv'), debug_driver)
    debugger.load_symbols(obj)

    ui = DebugUi(debugger)
    ui.open_all_source_files()
    ui.show()
    app.exec_()
    debugger.shutdown()
