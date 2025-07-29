#!/usr/bin/python

import sys
import argparse
import ppci.common
import logging
from ppci import api
from ppci.binutils.dbg import Debugger
from ppci.binutils.dbg.linux64debugdriver import Linux64DebugDriver
from dbgui import DebugUi, QtWidgets


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dut", help="The device under test, in this case an ELF-file"
    )
    parser.add_argument(
        "obj", help="The object file with the debug information"
    )
    args = parser.parse_args()
    dut = args.dut
    obj = args.obj

    logging.basicConfig(format=ppci.common.logformat, level=logging.DEBUG)
    app = QtWidgets.QApplication(sys.argv)

    linux_specific = Linux64DebugDriver()
    linux_specific.go_for_it([dut])
    debugger = Debugger(api.get_arch("x86_64"), linux_specific)
    debugger.load_symbols(obj)

    ui = DebugUi(debugger)
    ui.show()
    ui.logger.info("IDE started")
    app.exec_()
    debugger.shutdown()
