"""
    Debugger. The debugger always operates in remote mode like gdb.

    Start the debug server for your target and connect to it using the
    debugger interface.
"""

import logging
import cmd
import binascii
import struct
import time
import socket
import select
from ..api import get_arch, fix_object
from ..common import str2int, CompilerError
from .. import __version__ as ppci_version
from .disasm import Disassembler
from .debuginfo import DebugBaseType, DebugArrayType, DebugStructType
from .debuginfo import DebugInfo
from .debuginfo import DebugPointerType, DebugAddress, FpOffsetAddress
from .outstream import RecordingOutputStream
from ..lang.c3.builder import C3ExprParser
from ..lang.c3 import astnodes as c3nodes
from ..lang.c3 import Context as C3Context


# States:
STOPPED = 0
RUNNING = 1
FINISHED = 2


class TmpValue:
    """ Evaluated expression value.
        It has a value
        this value can be an actual value or an address (an lvalue)
        when lval is True, the value is a location,
        else it is the value itself
    """
    def __init__(self, value, lval, typ):
        self.value = value
        self.lval = lval
        self.typ = typ

    def __repr__(self):
        return 'TMP[0x{:X} {} {}]'.format(self.value, self.lval, self.typ)


class SubscribleEvent:
    def __init__(self):
        self.callbacks = []

    def fire(self, *args):
        for callback in self.callbacks:
            callback(*args)

    def subscribe(self, callback):
        self.callbacks.append(callback)


class Debugger:
    """
        Main interface to the debugger.
        Give it a target architecture for which it must debug
        and driver plugin to connect to hardware.
    """
    def __init__(self, arch, driver):
        self.arch = get_arch(arch)
        self.expr_parser = C3ExprParser(self.arch)
        self.disassembler = Disassembler(self.arch)
        self.driver = driver
        self.logger = logging.getLogger('dbg')
        self.connection_event = SubscribleEvent()
        self.state_event = SubscribleEvent()
        self.register_names = self.get_register_names()
        self.register_values = {rn: 0 for rn in self.register_names}
        self.debug_info = None
        self.variable_map = {}
        self.addr_map = {}

        # Subscribe to events:
        self.state_event.subscribe(self.on_halted)

        # Fire initial change:
        self.state_event.fire()

    def __repr__(self):
        return 'Debugger for {} using {}'.format(self.arch, self.driver)

    def on_halted(self):
        if self.is_halted:
            new_values = self.get_register_values(self.register_names)
            self.register_values.update(new_values)

    # Start stop parts:
    def run(self):
        """ Run the program """
        self.logger.info('run')
        self.driver.run()
        self.state_event.fire()

    def restart(self):
        self.logger.info('run')
        self.driver.restart()
        self.state_event.fire()

    def stop(self):
        """ Interrupt the currently running program """
        self.logger.info('stop')
        self.driver.stop()
        self.state_event.fire()

    def shutdown(self):
        pass

    def get_possible_breakpoints(self, filename):
        """ Return the rows in the file for which breakpoints can be set """
        options = set()
        for loc in self.debug_info.locations:
            if loc.loc.filename == filename:
                options.add(loc.loc.row)
        return options

    def set_breakpoint(self, filename, row):
        """ Set a breakpoint """
        self.logger.info('set breakpoint %s:%i', filename, row)
        address = self.find_address(filename, row)
        if address is None:
            self.logger.warn('Could not find address for breakpoint')
        self.driver.set_breakpoint(address)

    def clear_breakpoint(self, filename, row):
        """ Remove a breakpoint """
        self.logger.info('clear breakpoint %s:%i', filename, row)
        address = self.find_address(filename, row)
        if address is None:
            self.logger.warn('Could not find address for breakpoint')
        self.driver.clear_breakpoint(address)

    def step(self):
        """ Single step the debugged program """
        self.logger.info('step')
        self.driver.step()
        self.logger.info('program counter 0x%x', self.get_pc())
        self.state_event.fire()

    def get_status(self):
        return self.driver.get_status()

    status = property(get_status)

    @property
    def is_running(self):
        return self.status == RUNNING

    @property
    def is_halted(self):
        return not self.is_running

    # debug info:
    def load_symbols(self, obj):
        """ Load debug symbols from object file """
        obj = fix_object(obj)
        # verify the contents of the object with the memory image
        assert self.is_halted
        for image in obj.images:
            vdata = image.data
            adata = self.read_mem(image.location, len(vdata))
            if vdata == adata:
                self.logger.info('memory image %s validated!', image)
            else:
                self.logger.warning('Memory image %s mismatch!', image)

        if obj.debug_info:
            self.debug_info = obj.debug_info
        else:
            self.logger.warning('No debug information in object')
            self.debug_info = DebugInfo()

        self.obj = obj
        self.variable_map = {v.name: v for v in self.debug_info.variables}
        self.addr_map = {}
        for loc in self.debug_info.locations:
            addr = self.calc_address(loc.address)
            self.addr_map[addr] = loc
            self.logger.debug('%s at 0x%x', loc, addr)

    def calc_address(self, address):
        """ Calculate the actual address based on section and offset """
        if isinstance(address, DebugAddress):
            section = self.obj.get_section(address.section)
            return section.address + address.offset
        elif isinstance(address, FpOffsetAddress):
            return self.get_fp() + address.offset
        else:  # pragma: no cover
            raise NotImplementedError(str(address))

    def find_pc(self):
        """ Given the current program counter (pc) determine the source """
        if not self.debug_info:
            return
        pc = self.get_pc()
        if pc in self.addr_map:
            debug = self.addr_map[pc]
            self.logger.info('Found program counter at %s', debug)
            loc = debug.loc
            return loc.filename, loc.row

    def current_function(self):
        """ Determine the PC and then determine which function we are in """
        pc = self.get_pc()
        for function in self.debug_info.functions:
            begin = self.calc_address(function.begin)
            end = self.calc_address(function.end)
            if pc in range(begin, end):
                return function

    def local_vars(self):
        """ Return map of local variable names """
        cur_func = self.current_function()
        if not cur_func:
            return {}
        return {v.name: v for v in cur_func.variables}

    def find_address(self, filename, row):
        """ Given a filename and a row, determine the address """
        for debug in self.debug_info.locations:
            loc = debug.loc
            if loc.filename == filename and loc.row == row:
                return self.calc_address(debug.address)
        self.logger.warning('Could not find address for %s:%i', filename, row)

    # Registers:
    def get_register_names(self):
        return [reg.name for reg in self.arch.registers]

    def get_register_values(self, registers):
        """ Get a dictionary of register values """
        return self.driver.get_registers(registers)

    def get_registers(self):
        names = self.get_register_names()
        return self.get_register_values(names)

    def set_register(self, register, value):
        self.logger.info('Setting register {} to {}'.format(register, value))
        # TODO!

    # Memory:
    def read_mem(self, address, size):
        """ Read binary data from memory location """
        return self.driver.read_mem(address, size)

    def write_mem(self, address, data):
        """ Write binary data to memory location """
        return self.driver.write_mem(address, data)

    # Expressions:
    def eval_c3_str(self, expr):
        # Create a context for the expression to exist:
        context = C3Context(self.arch)

        # Parse expr:
        c3_expr = self.expr_parser.parse(expr, context)

        # Eval expr:
        val = self.eval_c3_expr(c3_expr)

        return val

    def sizeof(self, typ):
        """ Determine the size of a debug type """
        return typ.sizeof()
        # TODO: obsolete:
        if isinstance(typ, DebugBaseType):
            return typ.size
        elif isinstance(typ, DebugArrayType):
            return typ.size * self.sizeof(typ.element_type)
        elif isinstance(typ, DebugStructType):
            # TODO: handle alignment?
            return sum(self.sizeof(field[1]) for field in typ.fields)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))

    def eval_c3_expr(self, expr, rval=True):
        """ Evaluate C3 expression tree """
        # TODO: check types!!
        # TODO: merge with c3.scope stuff and c3 codegenerator stuff?
        assert isinstance(expr, c3nodes.Expression), str(type(expr))

        # Debug integer type, always 8 bytes, this is safe here
        # because this type must never be loaded!
        int_type = DebugBaseType('int', 8, 1)

        # See what to do:
        if isinstance(expr, c3nodes.Literal):
            if isinstance(expr.val, int):
                val = TmpValue(expr.val, False, int_type)
            else:
                raise CompilerError('Cannot use {}'.format(expr))
        elif isinstance(expr, c3nodes.Binop):
            # TODO: type coerce!
            a = self.eval_c3_expr(expr.a)
            b = self.eval_c3_expr(expr.b)
            if not isinstance(a.typ, DebugBaseType):
                raise CompilerError('{} of wrong type'.format(a))
            if not isinstance(b.typ, DebugBaseType):
                raise CompilerError('{} of wrong type'.format(b))
            opmp = {
                '+': lambda op1, op2: op1 + op2,
                '-': lambda op1, op2: op1 - op2,
                '*': lambda op1, op2: op1 * op2,
            }
            v = opmp[expr.op](a.value, b.value)
            val = TmpValue(v, False, int_type)
        elif isinstance(expr, c3nodes.Index):
            index = self.eval_c3_expr(expr.i)
            if not isinstance(index.typ, DebugBaseType):
                raise CompilerError('{} of wrong type'.format(index))
            base = self.eval_c3_expr(expr.base, rval=False)
            if not base.lval:
                raise CompilerError('{} is no location'.format(base))
            if not isinstance(base.typ, DebugArrayType):
                raise CompilerError('{} is no array'.format(base))
            element_size = self.sizeof(base.typ.element_type)
            addr = base.value + index.value * element_size
            val = TmpValue(addr, True, base.typ.element_type)
        elif isinstance(expr, c3nodes.Member):
            base = self.eval_c3_expr(expr.base, rval=False)
            if not base.lval:
                raise CompilerError('{} is no location'.format(base))
            if not isinstance(base.typ, DebugStructType):
                raise CompilerError('{} is no struct'.format(base))
            if not base.typ.has_field(expr.field):
                raise CompilerError(
                    '{} has no member {}'.format(base, expr.field))
            field = base.typ.get_field(expr.field)
            addr = base.value + field[2]
            val = TmpValue(addr, True, field[1])
        elif isinstance(expr, c3nodes.Deref):
            ptr = self.eval_c3_expr(expr.ptr)
            if not isinstance(ptr.typ, DebugPointerType):
                raise CompilerError(
                    'Cannot dereference non-pointer type {}'.format(ptr))
            val = TmpValue(ptr.value, True, ptr.typ.pointed_type)
        elif isinstance(expr, c3nodes.Unop):
            if expr.op == '&':
                rhs = self.eval_c3_expr(expr.a, rval=False)
                if not rhs.lval:
                    raise CompilerError(
                        'Cannot take address of {}'.format(expr.a))
                typ = DebugPointerType(rhs.typ)
                val = TmpValue(rhs.value, False, typ)
            elif expr.op in ['+', '-']:
                rhs = self.eval_c3_expr(expr.a)
                if not isinstance(rhs.typ, (DebugBaseType, DebugPointerType)):
                    raise CompilerError('{} of wrong type'.format(rhs))
                opmp = {
                    '-': lambda x: -x,
                    '+': lambda x: x
                }
                v = opmp[expr.op](rhs.value)
                val = TmpValue(v, False, rhs.typ)
            else:  # pragma: no cover
                raise NotImplementedError(str(expr))
        elif isinstance(expr, c3nodes.Identifier):
            # Fetch variable:
            name = expr.target
            local_vars = self.local_vars()
            if name in local_vars:
                var = local_vars[name]
                addr = self.calc_address(var.address)
                val = TmpValue(addr, True, var.typ)
            elif name in self.variable_map:
                var = self.variable_map[name]
                addr = self.calc_address(var.address)
                val = TmpValue(addr, True, var.typ)
            else:
                raise CompilerError('Cannot evaluate {}'.format(expr), None)
        else:  # pragma: no cover
            raise NotImplementedError('Cannot evaluate constant {}'
                                      .format(expr), None)
        if rval and val.lval:
            # Load variable now!
            loaded_val = self.load_value(val.value, val.typ)
            val = TmpValue(loaded_val, False, val.typ)
        return val

    def load_value(self, addr, typ):
        """ Load specific type from an address """
        # Load variable now!
        if not isinstance(typ, (DebugBaseType, DebugPointerType)):
            raise CompilerError('Cannot load {}'.format(typ))
        if isinstance(typ, DebugBaseType):
            size = typ.size
        else:
            size = self.arch.byte_sizes['ptr']  # Pointer size!
        fmts = {8: '<Q', 4: '<I', 2: '<H', 1: '<B'}
        fmt = fmts[size]
        loaded = self.read_mem(addr, size)
        loaded_val = struct.unpack(fmt, loaded)[0]
        return loaded_val

    def get_variable(self, name):
        """ Lookup variable with name in current symbols """
        if name in self.variable_map:
            return self.variable_map[name]

    # Disassembly:
    def get_pc(self):
        """ Get the program counter """
        return self.driver.get_pc()

    def get_fp(self):
        return self.driver.get_fp()

    def get_disasm(self):
        """ Get instructions around program counter """
        loc = self.get_pc()
        address = loc - 8
        data = self.read_mem(address, 16)
        instructions = []
        outs = RecordingOutputStream(instructions)
        self.disassembler.disasm(data, outs, address=address)
        return instructions

    def get_mixed(self):
        """ Get source lines and assembly lines """
        pass


class DebugDriver:  # pragma: no cover
    """
        Inherit this class to expose a target interface. This class implements
        primitives for a given hardware target.
    """
    def run(self):
        raise NotImplementedError()

    def step(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def get_status(self):
        raise NotImplementedError()

    def get_pc(self):
        raise NotImplementedError()

    def get_fp(self):
        raise NotImplementedError()

    def set_breakpoint(self, address):
        raise NotImplementedError()

    def get_registers(self, registers):
        """ Get the values for a range of registers """
        raise NotImplementedError()


class DummyDebugDriver(DebugDriver):
    def __init__(self):
        self.status = STOPPED

    def run(self):
        self.status = RUNNING

    def restart(self):
        self.status = RUNNING

    def step(self):
        pass

    def stop(self):
        self.status = STOPPED

    def get_status(self):
        return self.status

    def get_registers(self, registers):
        return {r: 0 for r in registers}

    def get_pc(self):
        return 0

    def get_fp(self):
        return 0

    def set_breakpoint(self, address):
        pass

    def clear_breakpoint(self, address):
        pass

    def read_mem(self, address, size):
        return bytes(size)

    def write_mem(self, address, data):
        pass


class GdbDebugDriver(DebugDriver):
    """ Implement debugging via the GDB remote interface.

    GDB servers can communicate via the RSP protocol.
    """
    def __init__(self):
        self.status = STOPPED
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(("localhost", 1234))
        self.timeout = 10
        self.retries = 3

    def pack(self, data):
        """ formats data into a RSP packet """
        for a, b in [(x, chr(ord(x) ^ 0x20)) for x in ['}','*','#','$']]:
            data = data.replace(a,'}%s' % b)
        return "$%s#%02X" % (data, (sum(ord(c) for c in data) % 256))

    def unpack(self, pkt):
        """ unpacks an RSP packet, returns the data"""
        if pkt[0:1]!=b'$' or pkt[-3:-2]!=b'#':
            raise ValueError('bad packet')
        if (sum(c for c in pkt[1:-3]) % 256) != int(pkt[-2:],16):
            raise ValueError('bad checksum')
        pkt = pkt[1:-3]
        return pkt

    def switch_endian(self, data):
        """ byte-wise reverses a hex encoded string """
        return ''.join(reversed(list(self.split_by_n(data, 2))))

    def split_by_n(self, seq, n):
        """ A generator to divide a sequence into chunks of n units.

        src: http://stackoverflow.com/questions/9475241/split-python-string-every-nth-character
        """
        while seq:
            yield seq[:n]
            seq = seq[n:]

    def sendpkt(self, data, retries=50):
        """ sends data via the RSP protocol to the device """
        self.get_status(0)
        self.s.send(self.pack(data).encode())
        res = None
        while not res:
            res = self.s.recv(1)
        discards = []
        while res!=b'+' and retries>0:
            discards.append(res)
            self.s.send(self.pack(data).encode())
            retries-=1
            res = self.s.recv(1)
        if len(discards)>0: print('send discards', discards)
        if retries==0:
            raise ValueError("retry fail")

    def readpkt(self, timeout=0):
        """ blocks until it reads an RSP packet, and returns it's
           data"""
        c=None
        discards=[]
        if timeout>0:
            start = time.time()
        while(c!=b'$'):
            if c: discards.append(c)
            c=self.s.recv(1)
            if timeout>0 and start+timeout < time.time():
                return
        if len(discards)>0: print('discards', discards)
        res=[c]

        while True:
            res.append(self.s.recv(1))
            if res[-1]==b'#' and res[-2]!=b"'":
                    res.append(self.s.recv(1))
                    res.append(self.s.recv(1))
                    try:
                        res=self.unpack(b''.join(res))
                    except:
                        self.s.send(b'-')
                        res=[]
                        continue
                    self.s.send(b'+')
                    return res

    def sendbrk(self):
        """ sends break command to the device """
        self.s.send(chr(0x03).encode())

    def get_pc(self):
        """ read the PC of the device"""
        self.sendpkt("p 20",self.retries)
        pc=int(self.switch_endian(self.readpkt(self.timeout).decode()),16)
        print("PC value read:%x"%pc)
        return(pc)

    def run(self):
        """start the device"""
        if(self.status==STOPPED):
            adr=self.get_pc()
            self.sendpkt("c%x"%adr)
        self.status = RUNNING

    def restart(self):
        """restart the device"""
        if(self.status==STOPPED):
             self.sendpkt("c00000080")
        self.status = RUNNING

    def step(self):
        """restart the device"""
        if(self.status==STOPPED):
             self.sendpkt("s")
             self.get_status(self.timeout)
             time.sleep(1)
             self.get_pc()

    def stop(self):
        self.sendbrk()
        self.status = STOPPED

    def get_status(self, timeout=5):
        if timeout > 0:
            start = time.time()
        readable, writable, exceptional = select.select([self.s], [], [], 0)
        while(readable==0):
            readable, writable, exceptional = select.select([self.s], [], [], 0)
            if timeout>0 and start+timeout < time.time():
                return
        if readable:
            res=self.readpkt(self.timeout)
            print(res)
            if(res==b"S05"):
                print("Target stopped..")
                self.status = STOPPED
                return(STOPPED)
            else:
                return(RUNNING)
        return self.status

    def get_registers(self, registers):
        self.sendpkt("g", 3)
        data = self.readpkt(3)
        res = {}
        for r in list(enumerate(registers)):
            res[r[1]] = binascii.unhexlify(self.switch_endian((data[r[0]*8:r[0]*8+8]).decode()))
        return res

    def set_breakpoint(self, address):
        self.sendpkt("Z0,%x,4" % address, self.retries)
        self.readpkt(self.timeout)

    def clear_breakpoint(self, address):
        self.sendpkt("z0,%x,4" % address, self.retries)
        self.readpkt(self.timeout)

    def read_mem(self, address, size):
        self.sendpkt("m %x,%x" % (address, size), self.retries)
        ret = binascii.unhexlify(self.readpkt(self.timeout))
        return ret

    def write_mem(self, address, data):
        length = len(data)
        data = self.switch_endian(binascii.hexlify(data).decode())
        self.sendpkt("M %x,%x:%s" % (address, length, data), self.retries)


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
        data = x[1]
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
        values = self.debugger.get_registers()
        for name, value in values.items():
            print(name, ':', value)

    def do_setbrk(self, arg):
        """ Set a breakpoint: setbrk filename, row """
        filename, row = arg.split(',')
        row=str2int(row)
        self.debugger.set_breakpoint(filename, row)

    def do_clrbrk(self, arg):
        """ Clear a breakpoint. Specify the location by "filename, row"
            for example:
            main.c, 5
        """
        filename, row = arg.split(',')
        row=str2int(row)
        self.debugger.clear_breakpoint(filename, row)

    def do_disasm(self, arg):
        """ Print disassembly around current location """
        instructions = self.debugger.get_disasm()
        for instruction in instructions:
            print(instruction)
