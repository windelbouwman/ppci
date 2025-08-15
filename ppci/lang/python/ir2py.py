"""Python back-end. Generates python code from ir-code."""

import math
import contextlib
import io
import struct
import logging
import time
from ... import ir
from ...graph import relooper


def literal_label(lit):
    """Invent a nice label name for the given literal"""
    return f"{lit.function.name}_{lit.name}"


def ir_to_python(ir_modules, f, reporter=None, runtime=True):
    """Convert ir-code to python code"""
    if reporter:
        f2 = f
        f = io.StringIO()

    generator = IrToPythonCompiler(f, reporter)
    generator.header()
    if runtime:
        generator.generate_runtime()
    for ir_module in ir_modules:
        if not isinstance(ir_module, ir.Module):
            raise TypeError("ir_modules must be list of ir.Module")
        generator.generate(ir_module)

    if reporter:
        source_code = f.getvalue()
        f2.write(source_code)
        reporter.dump_source("Python code", source_code)


def irpy_runtime_code(f):
    """Generate irpy runtime."""
    reporter = None
    generator = IrToPythonCompiler(f, reporter)
    generator.header()
    generator.generate_runtime()


class IrToPythonCompiler:
    """Can generate python script from ir-code"""

    logger = logging.getLogger("ir2py")

    def __init__(self, output_file, reporter):
        self.output_file = output_file
        self.reporter = reporter
        self.stack_size = 0
        self._level = 0

    def print(self, level, *args):
        """Print args to current file with level indents"""
        print("    " * level, end="", file=self.output_file)
        print(*args, file=self.output_file)

    def _indent(self):
        self._level += 1

    def _dedent(self):
        self._level -= 1

    @contextlib.contextmanager
    def func_def(self, decl: str):
        self.emit(f"def {decl}")
        self._indent()
        yield
        self._dedent()
        self.emit("")

    @contextlib.contextmanager
    def indented(self):
        self._indent()
        yield
        self._dedent()

    def emit(self, txt: str):
        """Emit python code at current indentation level"""
        self.print(self._level, txt)

    def header(self):
        """Emit a header suitable for in a python file"""
        self.emit(f"# Automatically generated on {time.ctime()}")
        self.emit(f"# Generator {__file__}")

    def generate_runtime(self):
        self.emit("")
        self.emit("import struct")
        self.emit("import math")
        # self.emit("import irpyrt")
        self.emit("")
        self.emit("class IrPy:")
        self._indent()
        self.emit("HEAP_START = 0x10000000")
        with self.func_def("__init__(self):"):
            self.emit("self.heap = bytearray()")
            self.emit("self.stack = bytearray()")
            self.emit("self.func_pointers = list()")
            self.emit("self.func_pointers.append(None)  # Null-entry")
            self.emit("self.f_ptrs_by_name = {}")
            self.emit("self.externals = {}")

        with self.func_def("clone(self):"):
            self.emit("x = IrPy()")
            self.emit("x.heap = self.heap")
            self.emit("x.func_pointers = self.func_pointers")
            self.emit("return x")

        with self.func_def("register_function(self, name, f):"):
            self.emit("idx = len(self.func_pointers)")
            self.emit("self.func_pointers.append(f)")
            self.emit("self.f_ptrs_by_name[name] = idx")
            self.emit("self.externals[name] = f")

        self.generate_builtins()
        self.generate_memory_builtins()
        self._dedent()
        self.emit("rt = IrPy()")

    def generate_memory_builtins(self):
        with self.func_def("read_mem(self, address, size):"):
            self.emit("mem, address = self.get_memory(address)")
            self.emit("assert address+size <= len(mem), str(hex(address))")
            self.emit("return mem[address:address+size]")

        with self.func_def("write_mem(self, address, data):"):
            self.emit("mem, address = self.get_memory(address)")
            self.emit("size = len(data)")
            self.emit("assert address+size <= len(mem), f'{hex(address)}'")
            self.emit("mem[address:address+size] = data")

        with self.func_def("get_memory(self, v):"):
            self.emit("if v >= self.HEAP_START:")
            with self.indented():
                self.emit("return self.heap, v - self.HEAP_START")
            self.emit("else:")
            with self.indented():
                self.emit("return self.stack, v")

        with self.func_def("heap_top(self):"):
            self.emit("return len(self.heap) + self.HEAP_START")

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
            assert struct.calcsize(fmt) == size
            # Generate load helpers:
            with self.func_def(f"load_{ty.name}(self, address):"):
                self.emit(f"data = self.read_mem(address, {size})")
                self.emit(f'return struct.unpack("{fmt}", data)[0]')

            # Generate store helpers:
            with self.func_def(f"store_{ty.name}(self, address, value):"):
                self.emit(f'data = struct.pack("{fmt}", value)')
                self.emit("self.write_mem(address, data)")

    def generate_builtins(self):
        # Wrap type helper:
        self.emit("@staticmethod")
        with self.func_def("correct(value, bits, signed):"):
            self.emit("base = 1 << bits")
            self.emit("value %= base")
            self.emit("if signed and value.bit_length() == bits:")
            with self.indented():
                self.emit("return value - base")
            self.emit("return value")

        # More C like integer divide
        self.emit("@staticmethod")
        with self.func_def("idiv(x, y):"):
            self.emit("sign = False")
            self.emit("if x < 0: x = -x; sign = not sign")
            self.emit("if y < 0: y = -y; sign = not sign")
            self.emit("v = x // y")
            self.emit("return -v if sign else v")

        # More c like remainder:
        # Note: sign of y is not relevant for result sign
        self.emit("@staticmethod")
        with self.func_def("irem(x, y):"):
            self.emit("if x < 0:")
            with self.indented():
                self.emit("x = -x")
                self.emit("sign = True")
            self.emit("else:")
            with self.indented():
                self.emit("sign = False")
            self.emit("if y < 0: y = -y")
            self.emit("v = x % y")
            self.emit("return -v if sign else v")

        # More c like shift left:
        self.emit("@staticmethod")
        with self.func_def("ishl(x, amount, bits):"):
            self.emit(r"amount = amount % bits")
            self.emit("return x << amount")

        # More c like shift right:
        self.emit("@staticmethod")
        with self.func_def("ishr(x, amount, bits):"):
            self.emit(r"amount = amount % bits")
            self.emit("return x >> amount")

        with self.func_def("alloca(self, amount):"):
            self.emit("ptr = len(self.stack)")
            self.emit("self.stack.extend(bytes(amount))")
            self.emit("return (ptr, amount)")

        with self.func_def("free(self, amount):"):
            self.emit("for _ in range(amount):")
            with self.indented():
                self.emit("self.stack.pop()")

    def generate(self, ir_mod):
        """Write ir-code to file f"""
        self.mod_name = ir_mod.name
        self.literals = []
        self.emit("")
        self.emit(f"# Module {ir_mod.name}")

        # Allocate room for global variables:
        for var in ir_mod.variables:
            self.generate_global_variable(var)

        # Generate functions:
        for function in ir_mod.functions:
            self.generate_function(function)

        # emit labeled literals:
        for lit in self.literals:
            label = literal_label(lit)
            self.emit(f"{label} = rt.heap_top()")
            for val in lit.data:
                self.emit(f"rt.heap.append({val})")
        self.emit("")

    def generate_global_variable(self, var):
        name = var.name
        self.emit(f"{name} = rt.heap_top()")
        if var.value:
            for part in var.value:
                if isinstance(part, bytes):
                    for byte in part:
                        self.emit(f"rt.heap.append({byte})")
                else:  # pragma: no cover
                    raise NotImplementedError()
        else:
            self.emit(f"rt.heap.extend(bytes({var.amount}))")
        self.emit(f"rt.externals['{name}'] = {name}")

    def generate_function(self, ir_function: ir.SubRoutine):
        """Generate a function to python code"""
        self.stack_size = 0
        name = ir_function.name
        args = ",".join(a.name for a in ir_function.arguments)
        with self.func_def(f"{name}({args}):"):
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
        self.emit(f"rt.register_function('{name}', {name})")
        self.emit("")

    def generate_shape(self, shape):
        """Generate python code for a shape structured program"""
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

    def generate_function_fallback(self, ir_function: ir.SubRoutine):
        """Generate a while-true with a switch-case on current block.

        This is a non-optimal, but always working strategy.
        """
        self.emit("_irpy_prev_block = None")
        self.emit(f"_irpy_current_block = '{ir_function.entry.name}'")
        self.emit("while True:")
        with self.indented():
            for block in ir_function.blocks:
                self.emit(f'if _irpy_current_block == "{block.name}":')
                with self.indented():
                    self.generate_block(block)
        self.emit("")

    def generate_block(self, block):
        """Generate code for one block"""
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
            self.emit(f"{phi_names} = {value_names}")

    def reset_stack(self):
        self.emit(f"rt.free({self.stack_size})")
        self.stack_size = 0

    def emit_jump(self, target: ir.Block):
        """Perform a jump in block mode."""
        assert isinstance(target, ir.Block)
        self.emit("_irpy_prev_block = _irpy_current_block")
        self.emit(f'_irpy_current_block = "{target.name}"')

    def generate_instruction(self, ins, block):
        """Generate python code for this instruction"""
        if isinstance(ins, ir.CJump):
            self.gen_cjump(ins)
        elif isinstance(ins, ir.Jump):
            self.gen_jump(ins)
        elif isinstance(ins, ir.Alloc):
            self.emit(f"{ins.name} = rt.alloca({ins.amount})")
            self.stack_size += ins.amount
        elif isinstance(ins, ir.AddressOf):
            src = self.fetch_value(ins.src)
            self.emit(f"{ins.name} = {src}[0]")
        elif isinstance(ins, ir.Const):
            self.gen_const(ins)
        elif isinstance(ins, ir.LiteralData):
            assert isinstance(ins.data, bytes)
            self.literals.append(ins)
            self.emit(f"{ins.name} = ({literal_label(ins)},{len(ins.data)})")
        elif isinstance(ins, ir.Unop):
            op = ins.operation
            a = self.fetch_value(ins.a)
            self.emit(f"{ins.name} = {op}{a}")
            if ins.ty.is_integer:
                self.emit(
                    f"{ins.name} = rt.correct({ins.name}, {ins.ty.bits}, {ins.ty.signed})"
                )
        elif isinstance(ins, ir.Binop):
            self.gen_binop(ins)
        elif isinstance(ins, ir.Cast):
            self.gen_cast(ins)
        elif isinstance(ins, ir.Store):
            self.gen_store(ins)
        elif isinstance(ins, ir.Load):
            self.gen_load(ins)
        elif isinstance(ins, ir.FunctionCall):
            args = ", ".join(self.fetch_value(a) for a in ins.arguments)
            callee = self._fetch_callee(ins.callee)
            self.emit(f"{ins.name} = {callee}({args})")
        elif isinstance(ins, ir.ProcedureCall):
            args = ", ".join(self.fetch_value(a) for a in ins.arguments)
            callee = self._fetch_callee(ins.callee)
            self.emit(f"{callee}({args})")
        elif isinstance(ins, ir.Phi):
            pass  # Phi is filled by predecessor
        elif isinstance(ins, ir.Return):
            self.reset_stack()
            self.emit(f"return {self.fetch_value(ins.result)}")
        elif isinstance(ins, ir.Exit):
            self.reset_stack()
            self.emit("return")
        elif isinstance(ins, ir.Undefined):
            self.emit(f"{ins.name} = 0")
        else:  # pragma: no cover
            self.emit(f"not implemented: {ins}")
            raise NotImplementedError(str(type(ins)))

    def gen_cjump(self, ins):
        a = self.fetch_value(ins.a)
        b = self.fetch_value(ins.b)
        if self._shape_style:
            raise NotImplementedError("TODO")
            # self.fill_phis(block)
            self.emit(f"if {a} {ins.cond} {b}:")
        else:
            self.emit(f"if {a} {ins.cond} {b}:")
            with self.indented():
                self.emit_jump(ins.lab_yes)
            self.emit("else:")
            with self.indented():
                self.emit_jump(ins.lab_no)

    def gen_jump(self, ins):
        if self._shape_style:
            raise NotImplementedError("TODO")
            # self.fill_phis(block)
            self.emit("pass")
        else:
            self.emit_jump(ins.target)

    def gen_cast(self, ins):
        if ins.ty.is_integer:
            self.emit(
                f"{ins.name} = rt.correct(int(round({ins.src.name})), {ins.ty.bits}, {ins.ty.signed})"
            )
        elif ins.ty is ir.ptr:
            self.emit(f"{ins.name} = int(round({ins.src.name}))")
        elif ins.ty in [ir.f32, ir.f64]:
            self.emit(f"{ins.name} = float({ins.src.name})")
        else:  # pragma: no cover
            raise NotImplementedError(str(ins))

    def gen_binop(self, ins):
        a = self.fetch_value(ins.a)
        b = self.fetch_value(ins.b)
        # Assume int for now.
        op = ins.operation
        int_ops = {"/": "rt.idiv", "%": "rt.irem"}

        shift_ops = {">>": "rt.ishr", "<<": "rt.ishl"}

        if op in int_ops and ins.ty.is_integer:
            fname = int_ops[op]
            self.emit(f"{ins.name} = {fname}({a}, {b})")
        elif op in shift_ops and ins.ty.is_integer:
            fname = shift_ops[op]
            self.emit(f"{ins.name} = {fname}({a}, {b}, {ins.ty.bits})")
        else:
            self.emit(f"{ins.name} = {a} {op} {b}")

        if ins.ty.is_integer:
            bits = ins.ty.bits
            signed = ins.ty.signed
            self.emit(f"{ins.name} = rt.correct({ins.name}, {bits}, {signed})")

    def gen_load(self, ins):
        address = self.fetch_value(ins.address)
        if isinstance(ins.ty, ir.BlobDataTyp):
            self.emit(f"{ins.name} = rt.read_mem({address}, {ins.ty.size})")
        else:
            self.emit(f"{ins.name} = rt.load_{ins.ty.name}({address})")

    def gen_store(self, ins):
        address = ins.address.name
        if isinstance(ins.value.ty, ir.BlobDataTyp):
            self.emit(
                f"rt.write_mem({address}, {ins.value.ty.size}, {ins.value.name})"
            )
        else:
            value = self.fetch_value(ins.value)
            self.emit(f"rt.store_{ins.value.ty.name}({address}, {value})")

    def gen_const(self, ins):
        if math.isinf(ins.value):
            if ins.value > 0:
                value = "math.inf"
            else:
                value = "-math.inf"
        else:
            value = str(ins.value)
        self.emit(f"{ins.name} = {value}")

    def _fetch_callee(self, callee):
        """Retrieves a callee and puts it into _fptr variable"""
        if isinstance(callee, ir.SubRoutine):
            expr = str(callee.name)
        elif isinstance(callee, ir.ExternalSubRoutine):
            expr = f"rt.externals['{callee.name}']"
        else:
            expr = f"rt.func_pointers[{callee.name}]"
        return expr

    def fetch_value(self, value):
        if isinstance(value, (ir.SubRoutine, ir.ExternalSubRoutine)):
            # Function pointer!
            expr = f"rt.f_ptrs_by_name['{value.name}']"
        elif isinstance(value, ir.ExternalVariable):
            expr = f"rt.externals['{value.name}']"
        else:
            expr = value.name
        return expr
