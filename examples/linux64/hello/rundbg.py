#!/usr/bin/python

from ppci import api
from ppci.binutils.dbg import Debugger
from ppci.binutils.dbg.ptcli import PtDebugCli
from ppci.binutils.dbg.linux64debugdriver import Linux64DebugDriver


if __name__ == '__main__':
    dut = 'hello'
    obj = 'hello.oj'

    linux_specific = Linux64DebugDriver()
    linux_specific.go_for_it([dut])
    debugger = Debugger(api.get_arch('x86_64'), linux_specific)
    debugger.load_symbols(obj)
    cli = PtDebugCli(debugger)
    cli.cmdloop()
