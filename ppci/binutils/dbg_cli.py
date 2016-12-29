""" Command line interface for the debugger """

import cmd
import binascii
from .. import __version__ as ppci_version
from ..common import str2int, CompilerError
from .dbg import STOPPED, RUNNING


class DebugCli(cmd.Cmd):
    """ Implement a console-based debugger interface. """
    prompt = '(ppci-dbg)> '
    intro = "ppci interactive debugger"

    def __init__(self, debugger):
        super().__init__()
        self.debugger = debugger

    def do_quit(self, _):
        """ Quit the debugger """
        return True

    do_q = do_quit

    def do_info(self, _):
        """ Show some info about the debugger """
        print('Debugger:     ', self.debugger)
        print('ppci version: ', ppci_version)
        text_status = {
            STOPPED: 'Stopped', RUNNING: 'Running'
        }
        print('Status:       ', text_status[self.debugger.status])

    def do_run(self, _):
        """ Continue the debugger """
        self.debugger.run()

    def do_step(self, _):
        """ Single step the debugger """
        self.debugger.step()

    do_s = do_step

    def do_stepi(self, _):
        """ Single instruction step the debugger """
        self.debugger.step()

    def do_nstep(self, count):
        """ Single instruction step the debugger """
        count = str2int(count)
        self.debugger.nstep(count)

    def do_stop(self, _):
        """ Stop the running program """
        self.debugger.stop()

    def do_restart(self, _):
        """ Restart the running program """
        self.debugger.restart()

    def do_read(self, arg):
        """ Read data from memory: read address,length"""
        address, size = map(str2int, arg.split(','))
        data = self.debugger.read_mem(address, size)
        data = binascii.hexlify(data).decode('ascii')
        print('Data @ 0x{:016X}: {}'.format(address, data))

    def do_write(self, arg):
        """ Write data to memory: write address,hexdata """
        address, data = arg.split(',')
        address = str2int(address)
        data = bytes(binascii.unhexlify(data.strip().encode('ascii')))
        self.debugger.write_mem(address, data)

    def do_print(self, arg):
        """ Print a variable """
        # Evaluate the given expression:
        try:
            tmp = self.debugger.eval_c3_str(arg)
            res = tmp.value
            print('$ = 0x{:X} [{}]'.format(res, tmp.typ))
        except CompilerError as ex:
            print(ex)

    do_p = do_print

    def do_readregs(self, _):
        """ Read registers """
        registers = self.debugger.get_registers()
        self.debugger.register_values = self.debugger.get_register_values(
            registers)
        for reg in registers:
            size = reg.bitsize // 4
            print('{:>5.5s} : 0x{:0{sz}X}'.format(
                str(reg), self.debugger.register_values[reg], sz=size))

    def do_writeregs(self, _):
        """ Write registers """
        self.debugger.set_register_values()

    def do_setreg(self, arg):
        """ Set registervalue """
        regnum, val = map(str2int, arg.split(','))
        self.debugger.register_values[self.debugger.num2regmap[regnum]] = val
        for reg in self.debugger.registers:
            size = reg.bitsize // 4
            print('{:>5.5s} : 0x{:0{sz}X}'.format(
                str(reg), self.debugger.register_values[reg], sz=size))

    def do_setbrk(self, arg):
        """ Set a breakpoint: setbrk filename, row """
        filename, row = arg.split(',')
        row = str2int(row)
        self.debugger.set_breakpoint(filename, row)

    def do_clrbrk(self, arg):
        """ Clear a breakpoint. Specify the location by "filename, row"
            for example:
            main.c, 5
        """
        filename, row = arg.split(',')
        row = str2int(row)
        self.debugger.clear_breakpoint(filename, row)

    def do_disasm(self, _):
        """ Print disassembly around current location """
        instructions = self.debugger.get_disasm()
        for instruction in instructions:
            print(instruction)
