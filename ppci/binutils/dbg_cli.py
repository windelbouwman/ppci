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

    def do_quit(self, arg):
        """ Quit the debugger """
        return True

    do_q = do_quit

    def do_info(self, arg):
        """ Show some info about the debugger """
        print('Debugger:     ', self.debugger)
        print('ppci version: ', ppci_version)
        text_status = {
            STOPPED: 'Stopped', RUNNING: 'Running'
        }
        print('Status:       ', text_status[self.debugger.status])

    def do_run(self, arg):
        """ Continue the debugger """
        self.debugger.run()

    def do_step(self, arg):
        """ Single step the debugger """
        self.debugger.step()

    do_s = do_step

    def do_stepi(self, arg):
        """ Single instruction step the debugger """
        self.debugger.step()

    def do_stop(self, arg):
        """ Stop the running program """
        self.debugger.stop()

    def do_restart(self, arg):
        """ Restart the running program """
        self.debugger.restart()

    def do_read(self, arg):
        """ Read data from memory: read address,length"""
        x = arg.split(',')
        address = str2int(x[0])
        size = str2int(x[1])
        data = self.debugger.read_mem(address, size)
        data = binascii.hexlify(data).decode('ascii')
        print('Data @ 0x{:016X}: {}'.format(address, data))

    def do_write(self, arg):
        """ Write data to memory: write address,hexdata """
        x = arg.split(',')
        address = str2int(x[0])
        data = x[1].strip()
        data = bytes(binascii.unhexlify(data.encode('ascii')))
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

    def do_regs(self, arg):
        """ Read registers """
        registers = self.debugger.get_registers()
        values = self.debugger.get_register_values(registers)
        for reg in registers:
            size = reg.bitsize // 4
            print('{:>5.5s} : 0x{:0{sz}X}'.format(str(reg), values[reg], sz=size))

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

    def do_disasm(self, arg):
        """ Print disassembly around current location """
        instructions = self.debugger.get_disasm()
        for instruction in instructions:
            print(instruction)
