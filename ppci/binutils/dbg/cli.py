""" Command line interface for the debugger """
import time
import cmd
import binascii
from threading import Lock
from ... import __version__ as ppci_version
from ...common import str2int, CompilerError
from .debug_driver import DebugState
import logging
import os
import sys
import time

if os.name == 'nt':
    from colorama import init


def pos(stdout, y, x):
    stdout.write('\x1b[%d;%dH' % (y, x))
    
def savepos(stdout):
    stdout.write('\x1b[s')

def restorepos(stdout):
    stdout.write('\x1b[u')


CMDLINE = 12
screenlock = Lock()

def clearscreen(stdout):
    stdout.write("\033[2J\033[1;1H")


def cleartocursor(stdout):
    stdout.write("\033[1J")


def clearaftercursor(stdout):
    stdout.write("\033[J")


def print_file_line(stdout, filename, lineno):
    lines = open(filename).read().splitlines()    
    s = "\033[37m\033[1mFile:{}\n".format(filename)    
    stdout.write(s)    
    s = "Line: [{} of {}]\n".format(lineno, len(lines))
    stdout.write(s)    
    s = "\033[0m\n"
    stdout.write(s)    
    s = "\033[0m\n"
    stdout.write(s)

    # Print a fragment of the file to show in context
    for i in range(lineno - 3, lineno + 3):
        if i < 1:            
            stdout.write('\n')
        elif i > len(lines):            
            stdout.write('\n')
        elif i == lineno:            
            s = "\033[33m\033[1m{}\033[32m->{}\033[0m\033[39m\n".format(str(i).rjust(4),lines[i - 1])
            stdout.write(s)
        else:            
            s = "\033[33m\033[1m{}\033[0m\033[39m  {}\n".format(str(i).rjust(4),lines[i - 1])
            stdout.write(s)
                  
class Proxy(object):
    logger = logging.getLogger('dbg') 
    def __init__(self, debugger):
        self.buffer = []
        self.debugger = debugger              
        self.stdout = sys.stdout
        
    def write(self, data):
        if len(data)>0:
            if data[-1] != '\n':
                self.buffer.append(data)
            else:
                if len(self.buffer):
                    self.flush()            
                with screenlock:		
                    self.stdout.write(data)
                    self.logger.debug('stdout writing: %s, [%s]', data, data.encode('utf-8').hex()) 
        
    
    def flush(self):                
        text = ''.join(self.buffer)
        self.buffer = []
        with screenlock:
            self.logger.debug('stdout flushing: %s, [%s] ', text, text.encode('utf-8').hex()) 
            self.stdout.write(text)
            self.stdout.flush()
            
       
            
            
    

class DebugCli(cmd.Cmd):
    """ Implement a console-based debugger interface. """
    prompt = 'DBG>'
    intro = "ppci interactive debugger"
    
    
    
    def __init__(self, debugger, showsource=False):
        self.Proxy = Proxy(debugger) 
        self.stdout_ori = sys.stdout                  
        sys.stdout = self.Proxy
        super().__init__(stdout=self.Proxy)        		
        self.debugger = debugger
        self.use_rawinput = False
        self.showsource = showsource            
        
        
        if self.showsource is True:
            if os.name == 'nt':
                init()
            clearscreen(sys.stdout)
            pos(sys.stdout,1, 1)
            if self.debugger.is_running:
                print('\033[37m\033[1mTarget State: RUNNING')
            else:
                print('\033[37m\033[1mTarget State: STOPPED')            
            pos(sys.stdout, CMDLINE, 1)
            self.debugger.events.on_stop += self.updatesourceview
            self.debugger.events.on_start += self.updatestatus
    
    
    
    
    def do_quit(self, _):
        """ Quit the debugger """
        sys.stdout = self.stdout_ori
        raise SystemExit
        return True

    do_q = do_quit

    def do_info(self, _):
        """ Show some info about the debugger """
        print('Architecture: ', self.debugger.arch)
        print('Debugger:     ', self.debugger)
        print('Debug driver: ', self.debugger.driver)
        print('ppci version: ', ppci_version)
        text_status = {
            DebugState.STOPPED: 'Stopped', DebugState.RUNNING: 'Running'
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
        if data:
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
        if self.debugger.register_values:
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

    def do_stepl(self, line):
        """ step one line """
        lastfunc = self.debugger.current_function()
        curfunc = lastfunc
        file, lastrow = self.debugger.find_pc()
        currow = lastrow
        while currow == lastrow or curfunc != lastfunc:
            self.do_stepi("")
            curfunc = self.debugger.current_function()
            file, currow = self.debugger.find_pc()

    do_sl = do_stepl

    def updatesourceview(self):
        if self.showsource is True and self.debugger.is_halted:
            with screenlock:
                savepos(self.stdout_ori)
                pos(self.stdout_ori, CMDLINE-1, 1)
                cleartocursor(self.stdout_ori)
                pos(self.stdout_ori, 1, 1)
                self.stdout_ori.write('\033[37m\033[1mTarget State: STOPPED\n')
                file, row = self.debugger.find_pc()
                pos(self.stdout_ori, 2, 1)
                print_file_line(self.stdout_ori, file, row)                
                restorepos(self.stdout_ori)
                self.stdout_ori.flush()            

    def updatestatus(self):
        with screenlock:
            savepos(self.stdout_ori)
            pos(self.stdout_ori, 1, 1)
            self.stdout_ori.write('\033[37m\033[1mTarget State: RUNNING\n')
            restorepos(self.stdout_ori)
            self.stdout_ori.flush()

    def precmd(self, line):                    
        pos(sys.stdout, CMDLINE + 1, 0)
        clearaftercursor(sys.stdout) 
        pos(sys.stdout, CMDLINE + 2, 0)
        return cmd.Cmd.precmd(self, line)

    def postcmd(self, stop, line):   
        pos(sys.stdout, CMDLINE + 1, 0)
        return cmd.Cmd.postcmd(self, stop, line)
        
