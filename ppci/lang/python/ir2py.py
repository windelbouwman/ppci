""" Python back-end. Generates python code from ir-code. """

import math
import contextlib
import io
import logging
import time
from ... import ir
from ...graph import relooper


def literal_label(lit):
    """ Invent a nice label name for the given literal """
    return "{}_{}".format(lit.function.name, lit.name)


def ir_to_python(ir_modules, f, reporter=None):
    """ Convert ir-code to python code """
    if reporter:
        f2 = f
        f = io.StringIO()

    generator = IrToPythonCompiler(f, reporter)
    generator.header()
    for ir_module in ir_modules:
        if not isinstance(ir_module, ir.Module):
            raise TypeError("ir_modules must be list of ir.Module")
        generator.generate(ir_module)

    if reporter:
        source_code = f.getvalue()
        f2.write(source_code)
        reporter.dump_source("Python code", source_code)


class IrToPythonCompiler:
    """ Can generate python script from ir-code """

    logger = logging.getLogger("ir2py")

    def __init__(self, output_file, reporter):
        self.output_file = output_file
        self.reporter = reporter
        self.stack_size = 0
        self.func_ptr_map = {}
        self._level = 0

    def print(self, level, *args):
        """ Print args to current file with level indents """
        print("    " * level, end="", file=self.output_file)
        print(*args, file=self.output_file)

    def _indent(self):
        self._level += 1

    def _dedent(self):
        self._level -= 1

    @contextlib.contextmanager
    def indented(self):
        self._indent()
        yield
        self._dedent()

    def emit(self, txt):
        """ Emit python code at current indentation level """
        self.print(self._level, txt)

    def header(self):
        """ Emit a header suitable for in a python file """
        self.emit("# Automatically generated on {}".format(time.ctime()))
        self.emit("# Generator {}".format(__file__))
        self.emit("")
        self.emit("import struct")
        self.emit("import math")
        self.emit("")
        self.emit("_irpy_heap = bytearray()")
        self.emit("_irpy_stack = bytearray()")
        self.emit("HEAP_START = 0x10000000")
        self.emit("_irpy_func_pointers = list()")
        self.emit("_irpy_externals = {}")
        self.emit("")

        self.generate_builtins()
        self.generate_memory_builtins()

    def generate_memory_builtins(self):
        self.emit("def read_mem(address, size):")
        with self.indented():
            self.emit("mem, address = _irpy_get_memory(address)")
            self.emit("assert address+size <= len(mem), str(hex(address))")
            self.emit("return mem[address:address+size]")
        self.emit("")

        self.emit("def write_mem(address, data):")
        with self.indented():
            self.emit("mem, address = _irpy_get_memory(address)")
            self.emit("size = len(data)")
            self.emit("assert address+size <= len(mem), str(hex(address))")
            self.emit("mem[address:address+size] = data")
        self.emit("")

        self.emit("def _irpy_get_memory(v):")
        self.print(1, "if v >= HEAP_START:")
        self.print(2, "return _irpy_heap, v - HEAP_START")
        self.print(1, "else:")
        self.print(2, "return _irpy_stack, v")
        self.emit("")

        self.emit("def _irpy_heap_top():")
        with self.indented():
            self.emit("return len(_irpy_heap) + HEAP_START")
        self.emit("")

        # Generate load functions:
        foo = [
            (ir.f64, "d", 8),
            (ir.f32, "f", 4),
            (ir.i64, "q", 8),
            (ir.u64, "Q", 8),
            (ir.i32, "i", 4),
            (ir.u32, "I", 4),
            (ir.ptr, "i", 4),
            (ir.i16, "h", 2),
            (ir.u16, "H", 2),
            (ir.i8, "b", 1),
            (ir.u8, "B", 1),
        ]

        for ty, fmt, size in foo:
            # Generate load helpers:
            self.emit("def load_{}(p):".format(ty.name))
            self.print(
                1,
                'return struct.unpack("{0}", read_mem(p, {1}))[0]'.format(
                    fmt, size
                ),
            )
            self.emit("")

            # Generate store helpers:
            self.emit("def store_{}(v, p):".format(ty.name))
            self.print(1, 'write_mem(p, struct.pack("{0}", v))'.format(fmt))
            self.emit("")

    def generate_builtins(self):
        # Wrap type helper:
        self.emit("def _irpy_correct(value, bits, signed):")
        self.print(1, "base = 1 << bits")
        self.print(1, "value %= base")
        self.print(1, "if signed and value.bit_length() == bits:")
        self.print(2, "return value - base")
        self.print(1, "else:")
        self.print(2, "return value")
        self.emit("")

        # More C like integer divide
        self.emit("def _irpy_idiv(x, y):")
        with self.indented():
            self.emit("sign = False")
            self.emit("if x < 0: x = -x; sign = not sign")
            self.emit("if y < 0: y = -y; sign = not sign")
            self.emit("v = x // y")
            self.emit("return -v if sign else v")
        self.emit("")

        # More c like remainder:
        # Note: sign of y is not relevant for result sign
        self.emit("def _irpy_irem(x, y):")
        self.print(1, "if x < 0:")
        self.print(2, "x = -x")
        self.print(2, "sign = True")
        self.print(1, "else:")
        self.print(2, "sign = False")
        self.print(1, "if y < 0: y = -y")
        self.print(1, "v = x % y")
        self.print(1, "return -v if sign else v")
        self.emit("")

        # More c like shift left:
        self.emit("def _irpy_ishl(x, amount, bits):")
        with self.indented():
            self.emit("amount = amount % bits")
            self.emit("return x << amount")
        self.emit("")

        # More c like shift right:
        self.emit("def _irpy_ishr(x, amount, bits):")
        with self.indented():
            self.emit("amount = amount % bits")
            self.emit("return x >> amount")
        self.emit("")

        self.emit("def _irpy_alloca(amount):")
        with self.indented():
            self.emit("ptr = len(_irpy_stack)")
            self.emit("_irpy_stack.extend(bytes(amount))")
            self.emit("return (ptr, amount)")
        self.emit("")

        self.emit("def _irpy_free(amount):")
        self.print(1, "for _ in range(amount):")
        self.print(2, "_irpy_stack.pop()")
        self.emit("")

    def generate(self, ir_mod):
        """ Write ir-code to file f """
        self.mod_name = ir_mod.name
        self.literals = []
        self.emit("")
        self.emit("# Module {}".format(ir_mod.name))

        # Allocate room for global variables:
        for var in ir_mod.variables:
            self.emit("{} = _irpy_heap_top()".format(var.name))
            if var.value:
                for part in var.value:
                    if isinstance(part, bytes):
                        for byte in part:
                            self.emit("_irpy_heap.append({})".format(byte))
                    else:  # pragma: no cover
                        raise NotImplementedError()
            else:
                self.emit("_irpy_heap.extend(bytes({}))".format(var.amount))

        # Generate functions:
        for function in ir_mod.functions:
            self.generate_function(function)

        # emit labeled literals:
        for lit in self.literals:
            self.emit("{} = _irpy_heap_top()".format(literal_label(lit)))
            for val in lit.data:
                self.emit("_irpy_heap.append({})".format(val))
        self.emit("")

    def generate_function(self, ir_function):
        """ Generate a function to python code """
        self.stack_size = 0
        args = ",".join(a.name for a in ir_function.arguments)
        self.emit("def {}({}):".format(ir_function.name, args))
        with self.indented():
            # TODO: enable shape style:
            # try:
            #     # TODO: remove this to enable shape style:
            #     raise ValueError
            #     shape, _rmap = relooper.find_structure(ir_function)
            #     src = io.StringIO()
            #     relooper.print_shape(shape, file=src)
            #     self.reporter.dump_source(ir_function.name, src.getvalue())
            #     self._rmap = _rmap
            #     self._shape_style = True
            #     self.generate_shape(shape)
            # except ValueError:
            self.logger.debug("Falling back to block-switch-style")
            # Fall back to block switch stack!
            self._shape_style = False
            self.generate_function_fallback(ir_function)

        # Register function for function pointers:
        self.emit("_irpy_func_pointers.append({})".format(ir_function.name))
        self.func_ptr_map[ir_function] = len(self.func_ptr_map)
        self.emit("")

    def generate_shape(self, shape):
        """ Generate python code for a shape structured program """
        if isinstance(shape, relooper.BasicShape):
            self.generate_block(self._rmap[shape.content])
        elif isinstance(shape, relooper.SequenceShape):
            if shape.shapes:
                for sub_shape in shape.shapes:
                    self.generate_shape(sub_shape)
            else:
                self.emit("pass")
        elif isinstance(shape, relooper.IfShape):
            blk = self._rmap[shape.content]
            self.generate_block(blk)
            with self.indented():
                if shape.yes_shape:
                    self.generate_shape(shape.yes_shape)
                else:
                    self.emit("pass")
            if shape.no_shape:
                self.emit("else:")
                with self.indented():
                    self.generate_shape(shape.no_shape)
        elif isinstance(shape, relooper.LoopShape):
            self.emit("while True:")
            with self.indented():
                self.generate_shape(shape.body)
        elif isinstance(shape, relooper.ContinueShape):
            self.emit("continue")
        elif isinstance(shape, relooper.BreakShape):
            self.emit("break")
        elif shape is None:
            self.emit("pass")
        else:  # pragma: no cover
            raise NotImplementedError(str(shape))

    def generate_function_fallback(self, ir_function):
        """ Generate a while-true with a switch-case on current block.

        This is a non-optimal, but always working strategy.
        """
        self.emit("_irpy_prev_block = None")
        self.emit("_irpy_current_block = '{}'".format(ir_function.entry.name))
        self.emit("while True:")
        with self.indented():
            for block in ir_function.blocks:
                self.emit('if _irpy_current_block == "{}":'.format(block.name))
                with self.indented():
                    self.generate_block(block)
        self.emit("")

    def generate_block(self, block):
        """ Generate code for one block """
        for ins in block:
            self.generate_instruction(ins, block)

        if not self._shape_style:
            self.fill_phis(block)

    def fill_phis(self, block):
        # Generate eventual phi fill code:
        phis = [p for s in block.successors for p in s.phis]
        if phis:
            phi_names = ", ".join(p.name for p in phis)
            value_names = ", ".join(p.inputs[block].name for p in phis)
            self.emit("{} = {}".format(phi_names, value_names))

    def reset_stack(self):
        self.emit("_irpy_free({})".format(self.stack_size))
        self.stack_size = 0

    def emit_jump(self, target: ir.Block):
        """ Perform a jump in block mode. """
        assert isinstance(target, ir.Block)
        self.emit("_irpy_prev_block = _irpy_current_block")
        self.emit('_irpy_current_block = "{}"'.format(target.name))

    def generate_instruction(self, ins, block):
        """ Generate python code for this instruction """
        if isinstance(ins, ir.CJump):
            self.gen_cjump(ins)
        elif isinstance(ins, ir.Jump):
            self.gen_jump(ins)
        elif isinstance(ins, ir.Alloc):
            self.emit("{} = _irpy_alloca({})".format(ins.name, ins.amount))
            self.stack_size += ins.amount
        elif isinstance(ins, ir.AddressOf):
            src = self.fetch_value(ins.src)
            self.emit("{} = {}[0]".format(ins.name, src))
        elif isinstance(ins, ir.Const):
            self.gen_const(ins)
        elif isinstance(ins, ir.LiteralData):
            assert isinstance(ins.data, bytes)
            self.literals.append(ins)
            self.emit(
                "{} = ({},{})".format(
                    ins.name, literal_label(ins), len(ins.data)
                )
            )
        elif isinstance(ins, ir.Unop):
            op = ins.operation
            a = self.fetch_value(ins.a)
            self.emit("{} = {}{}".format(ins.name, op, ins.a.name))
            if ins.ty.is_integer:
                self.emit(
                    "{0} = _irpy_correct({0}, {1}, {2})".format(
                        ins.name, ins.ty.bits, ins.ty.signed
                    )
                )
        elif isinstance(ins, ir.Binop):
            self.gen_binop(ins)
        elif isinstance(ins, ir.Cast):
            if ins.ty.is_integer:
                self.emit(
                    "{} = _irpy_correct(int(round({})), {}, {})".format(
                        ins.name, ins.src.name, ins.ty.bits, ins.ty.signed
                    )
                )
            elif ins.ty is ir.ptr:
                self.emit("{} = int(round({}))".format(ins.name, ins.src.name))
            elif ins.ty in [ir.f32, ir.f64]:
                self.emit("{} = float({})".format(ins.name, ins.src.name))
            else:  # pragma: no cover
                raise NotImplementedError(str(ins))
        elif isinstance(ins, ir.Store):
            self.gen_store(ins)
        elif isinstance(ins, ir.Load):
            self.gen_load(ins)
        elif isinstance(ins, ir.FunctionCall):
            args = ", ".join(self.fetch_value(a) for a in ins.arguments)
            callee = self._fetch_callee(ins.callee)
            self.emit("{} = {}({})".format(ins.name, callee, args))
        elif isinstance(ins, ir.ProcedureCall):
            args = ", ".join(self.fetch_value(a) for a in ins.arguments)
            callee = self._fetch_callee(ins.callee)
            self.emit("{}({})".format(callee, args))
        elif isinstance(ins, ir.Phi):
            pass  # Phi is filled by predecessor
        elif isinstance(ins, ir.Return):
            self.reset_stack()
            self.emit("return {}".format(self.fetch_value(ins.result)))
        elif isinstance(ins, ir.Exit):
            self.reset_stack()
            self.emit("return")
        elif isinstance(ins, ir.Undefined):
            self.emit("{} = 0".format(ins.name))
        else:  # pragma: no cover
            self.emit("not implemented: {}".format(ins))
            raise NotImplementedError(str(type(ins)))

    def gen_cjump(self, ins):
        a = self.fetch_value(ins.a)
        b = self.fetch_value(ins.b)
        if self._shape_style:
            self.fill_phis(block)
            self.emit("if {} {} {}:".format(a, ins.cond, b))
        else:
            self.emit("if {} {} {}:".format(a, ins.cond, b))
            with self.indented():
                self.emit_jump(ins.lab_yes)
            self.emit("else:")
            with self.indented():
                self.emit_jump(ins.lab_no)

    def gen_jump(self, ins):
        if self._shape_style:
            self.fill_phis(block)
            self.emit("pass")
        else:
            self.emit_jump(ins.target)

    def gen_binop(self, ins):
        a = self.fetch_value(ins.a)
        b = self.fetch_value(ins.b)
        # Assume int for now.
        op = ins.operation
        int_ops = {"/": "_irpy_idiv", "%": "_irpy_irem"}

        shift_ops = {">>": "_irpy_ishr", "<<": "_irpy_ishl"}

        if op in int_ops and ins.ty.is_integer:
            fname = int_ops[op]
            self.emit("{} = {}({}, {})".format(ins.name, fname, a, b))
        elif op in shift_ops and ins.ty.is_integer:
            fname = shift_ops[op]
            self.emit(
                "{} = {}({}, {}, {})".format(
                    ins.name, fname, a, b, ins.ty.bits
                )
            )
        else:
            self.emit("{} = {} {} {}".format(ins.name, a, op, b))

        if ins.ty.is_integer:
            self.emit(
                "{0} = _irpy_correct({0}, {1}, {2})".format(
                    ins.name, ins.ty.bits, ins.ty.signed
                )
            )

    def gen_load(self, ins):
        address = self.fetch_value(ins.address)
        if isinstance(ins.ty, ir.BlobDataTyp):
            self.emit(
                "{0} = read_mem({1}, {2})".format(
                    ins.name, address, ins.ty.size
                )
            )
        else:
            self.emit(
                "{0} = load_{1}({2})".format(ins.name, ins.ty.name, address)
            )

    def gen_store(self, ins):
        if isinstance(ins.value.ty, ir.BlobDataTyp):
            self.emit(
                "write_mem({0}, {1}, {2})".format(
                    ins.address.name, ins.value.ty.size, ins.value.name
                )
            )
        else:
            v = self.fetch_value(ins.value)
            self.emit(
                "store_{0}({2}, {1})".format(
                    ins.value.ty.name, ins.address.name, v
                )
            )

    def gen_const(self, ins):
        if math.isinf(ins.value):
            if ins.value > 0:
                value = "math.inf"
            else:
                value = "-math.inf"
        else:
            value = str(ins.value)
        self.emit("{} = {}".format(ins.name, value))

    def _fetch_callee(self, callee):
        """ Retrieves a callee and puts it into _fptr variable """
        if isinstance(callee, ir.SubRoutine):
            expr = "{}".format(callee.name)
        elif isinstance(callee, ir.ExternalSubRoutine):
            expr = "_irpy_externals['{}']".format(callee.name)
        else:
            expr = "_irpy_func_pointers[{}]".format(callee.name)
        return expr

    def fetch_value(self, value):
        if isinstance(value, ir.SubRoutine):
            # Function pointer!
            fidx = self.func_ptr_map[value]
            expr = str(fidx)
        elif isinstance(value, ir.ExternalVariable):
            expr = "_irpy_externals['{}']".format(value.name)
        else:
            expr = value.name
        return expr
