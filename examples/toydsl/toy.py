import logging
import struct
from textx.metamodel import metamodel_from_file
from ppci import ir
from ppci.irutils import verify_module
from ppci import api


def pack_string(txt):
    ln = struct.pack("<Q", len(txt))
    return ln + txt.encode("ascii")


class TcfCompiler:
    """Compiler for the Tcf language"""

    logger = logging.getLogger("tcfcompiler")

    def __init__(self):
        self.int_size = 8
        self.int_type = ir.i64
        self.toy_mm = metamodel_from_file("toy.tx")
        self.toy_mm.register_obj_processors(
            {
                "PrintStatement": self.handle_print,
                "AssignmentStatement": self.handle_assignment,
                "Expression": self.handle_expression,
                "Sum": self.handle_sum,
                "Product": self.handle_product,
            }
        )

    def compile(self, filename):
        self.variables = {}

        # Prepare the module:
        ir_module = ir.Module("toy")
        self.io_print2 = ir.ExternalProcedure(
            "io_print2", [ir.ptr, self.int_type]
        )
        ir_module.add_external(self.io_print2)
        ir_function = ir.Procedure("toy_toy", ir.Binding.GLOBAL)
        ir_module.add_function(ir_function)
        self.ir_block = ir.Block("entry")
        ir_function.entry = self.ir_block
        ir_function.add_block(self.ir_block)

        # Load the program:
        self.toy_mm.model_from_file("example.tcf")

        # Close the procedure:
        self.emit(ir.Exit())

        verify_module(ir_module)
        return ir_module

    def emit(self, instruction):
        self.ir_block.add_instruction(instruction)
        return instruction

    def handle_print(self, print_statement):
        self.logger.debug("print statement %s", print_statement.var)
        name = print_statement.var
        value = self.load_var(name)
        label_data = pack_string("{} :".format(name))
        label = self.emit(ir.LiteralData(label_data, "label"))
        label_ptr = self.emit(ir.AddressOf(label, "label_ptr"))
        self.emit(ir.ProcedureCall(self.io_print2, [label_ptr, value]))

    def handle_assignment(self, assignment):
        self.logger.debug("assign %s = %s", assignment.var, assignment.expr)
        name = assignment.var
        assert isinstance(name, str)

        # Create the variable on stack, if not already present:
        if name not in self.variables:
            alloc = self.emit(
                ir.Alloc(name + "_alloc", self.int_size, self.int_size)
            )
            addr = self.emit(ir.AddressOf(alloc, name + "_addr"))
            self.variables[name] = addr
        mem_loc = self.variables[name]
        value = assignment.expr.ir_value
        self.emit(ir.Store(value, mem_loc))

    def handle_expression(self, expr):
        self.logger.debug("expression")
        expr.ir_value = expr.val.ir_value

    def handle_sum(self, sum):
        """Process a sum element"""
        self.logger.debug("sum")
        lhs = sum.base.ir_value
        for term in sum.terms:
            op = term.operator
            rhs = term.value.ir_value
            lhs = self.emit(ir.Binop(lhs, op, rhs, "sum", self.int_type))
        sum.ir_value = lhs

    def handle_product(self, product):
        self.logger.debug("product")
        lhs = self.get_value(product.base)
        for factor in product.factors:
            rhs = self.get_value(factor.value)
            lhs = self.emit(ir.Binop(lhs, "*", rhs, "prod", self.int_type))
        product.ir_value = lhs

    def get_value(self, value):
        if isinstance(value, int):
            ir_value = self.emit(ir.Const(value, "constant", self.int_type))
        elif isinstance(value, str):
            ir_value = self.load_var(value)
        else:  # It must be an expression!
            ir_value = value.ir_value
        return ir_value

    def load_var(self, var_name):
        mem_loc = self.variables[var_name]
        return self.emit(ir.Load(mem_loc, var_name, self.int_type))


tcf_compiler = TcfCompiler()
ir_module = tcf_compiler.compile("example.tcf")

obj1 = api.ir_to_object([ir_module], "x86_64")
obj2 = api.c3c(["bsp.c3", "../../librt/io.c3"], [], "x86_64")
obj3 = api.asm("linux.asm", "x86_64")
obj = api.link([obj1, obj2, obj3], layout="layout.mmap")

print(obj)
with open("example.oj", "w") as f:
    obj.save(f)

# Create a linux elf file:
api.objcopy(obj, "code", "elf", "example")
