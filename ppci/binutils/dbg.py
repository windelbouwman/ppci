"""
    Debugger. The debugger always operates in remote mode like gdb.

    Start the debug server for your target and connect to it using the
    debugger interface.
"""

import logging
import cmd
import binascii
import struct
from ..api import get_arch, fix_object
from ..common import str2int, CompilerError
from .. import version as ppci_version
from .disasm import Disassembler
from .debuginfo import DebugBaseType, DebugArrayType, DebugStructType
from .debuginfo import DebugPointerType
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
        self.logger.info('run')
        self.driver.run()
        self.state_event.fire()

    def restart(self):
        self.logger.info('run')
        self.driver.restart()
        self.state_event.fire()

    def stop(self):
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
        self.logger.info('set breakpoint %s:%i', filename, row)
        address = self.find_address(filename, row)
        if address is None:
            self.logger.warn('Could not find address for breakpoint')
        self.driver.set_breakpoint(address)

    def clear_breakpoint(self, filename, row):
        self.logger.info('clear breakpoint %s:%i', filename, row)
        address = self.find_address(filename, row)
        if address is None:
            self.logger.warn('Could not find address for breakpoint')
        self.driver.clear_breakpoint(address)

    def step(self):
        self.logger.info('step')
        self.driver.step()
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
            #assert vdata == adata
        self.logger.info('memory image validated!')
        self.debug_info = obj.debug_info
        self.obj = obj
        self.variable_map = {v.name: v for v in self.debug_info.variables}
        # print(self.variable_map)

    def calc_address(self, address):
        section = self.obj.get_section(address.section)
        return section.address + address.offset

    def find_pc(self):
        """ Given the current program counter (pc) determine the source """
        if not self.debug_info:
            return
        pc = self.get_pc()
        for debug in self.debug_info.locations:
            # print(debug)
            addr = self.calc_address(debug.address)
            if pc == addr:
                print('MATCH', debug)
                loc = debug.loc
                return loc.filename, loc.row

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
        return self.driver.read_mem(address, size)

    def write_mem(self, address, data):
        return self.driver.write_mem(address, data)

    # Expressions:
    def eval_str(self, expr):
        # Create a context for the expression to exist:
        context = C3Context(self.arch)

        # Parse expr:
        c3_expr = self.expr_parser.parse(expr, context)

        # Eval expr:
        val = self.eval_expr(c3_expr)

        return val

    def sizeof(self, typ):
        """ Determine the size of a debug type """
        if isinstance(typ, DebugBaseType):
            return typ.size
        elif isinstance(typ, DebugArrayType):
            return typ.size * self.sizeof(typ.element_type)
        elif isinstance(typ, DebugStructType):
            # TODO: handle alignment?
            return sum(self.sizeof(field[1]) for field in typ.fields)
        else:
            raise NotImplementedError(str(typ))

    def eval_expr(self, expr, rval=True):
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
            a = self.eval_expr(expr.a)
            b = self.eval_expr(expr.b)
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
            index = self.eval_expr(expr.i)
            if not isinstance(index.typ, DebugBaseType):
                raise CompilerError('{} of wrong type'.format(index))
            base = self.eval_expr(expr.base, rval=False)
            if not base.lval:
                raise CompilerError('{} is no location'.format(base))
            if not isinstance(base.typ, DebugArrayType):
                raise CompilerError('{} is no array'.format(base))
            element_size = self.sizeof(base.typ.element_type)
            addr = base.value + index.value * element_size
            val = TmpValue(addr, True, base.typ.element_type)
        elif isinstance(expr, c3nodes.Member):
            base = self.eval_expr(expr.base, rval=False)
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
            ptr = self.eval_expr(expr.ptr)
            if not isinstance(ptr.typ, DebugPointerType):
                raise CompilerError(
                    'Cannot dereference non-pointer type {}'.format(ptr))
            val = TmpValue(ptr.value, True, ptr.typ.pointed_type)
        elif isinstance(expr, c3nodes.Unop):
            if expr.op == '&':
                rhs = self.eval_expr(expr.a, rval=False)
                if not rhs.lval:
                    raise CompilerError(
                        'Cannot take address of {}'.format(expr.a))
                typ = DebugPointerType(rhs.typ)
                val = TmpValue(rhs.value, False, typ)
            elif expr.op in ['+', '-']:
                rhs = self.eval_expr(expr.a)
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
            if name in self.variable_map:
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
        fmts = {
            8: '<Q', 4: '<I', 2: '<H', 1: '<B',
        }
        if isinstance(typ, DebugBaseType):
            size = typ.size
        else:
            size = self.arch.byte_sizes['ptr']  # Pointer size!
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
        return 0

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

    def set_breakpoint(self, address):
        pass
        
    def clear_breakpoint(self, address):
        pass

    def read_mem(self, address, size):
        return bytes(size)

    def write_mem(self, address, data):
        pass


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
            tmp = self.debugger.eval_str(arg)
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
