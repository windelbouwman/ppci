from ... import ir
from ...graph.relooper import find_structure
from .nodes import types, declarations, expressions, statements


class CSynthesizer:
    """ Take an IR-module and convert it into a C-AST.

    This does essentially the opposite of the codegenerator. """

    def __init__(self):
        self.var_map = {}
        self.block_map = {}
        self.void_type = types.BasicType(types.BasicType.VOID)
        self.voidptr_type = types.PointerType(self.void_type)

    def syn_module(self, ir_module):
        for function in ir_module.functions:
            self.syn_function(function)

    def syn_function(self, function):
        shape, block_map = find_structure(function)
        for block in function:
            self.syn_block(block)

    def syn_block(self, block):
        """ Synthesize an ir block into C """
        self._inner_statements = []
        for instruction in block:
            self.syn_instruction(instruction)
        loc = None
        compound = statements.Compound(self._inner_statements, loc)
        statements.Label(block.name, compound, None)

    def emit_statement(self, statement):
        self._inner_statements.append(statement)

    def emit_expression(self, expression):
        self.emit_statement(statements.ExpressionStatement(expression))

    def emit_store(self, lhs, rhs):
        typ = self.get_ctype()
        expression = expressions.BinaryOperator(lhs, "=", rhs, typ, True, None)
        self.emit_expression(expression)

    def get_var(self, ir_val):
        if ir_val not in self.var_map:
            # Create a variable now.
            loc = None
            typ = self.voidptr_type
            var = declarations.VariableDeclaration(
                None, typ, ir_val.name, None, loc
            )
            self.var_map[ir_val] = var
        return self.var_map[ir_val]

    def get_var_ref(self, ir_val):
        var = self.get_var(ir_val)
        typ = self.voidptr_type
        loc = None
        access = expressions.VariableAccess(var, typ, True, loc)
        return access

    def get_ctype(self):
        typ = self.voidptr_type
        return typ

    def syn_instruction(self, instruction):
        """ Convert ir instruction to its corresponding C counterpart """
        if isinstance(instruction, ir.Alloc):
            ctyp = types.BasicType(types.BasicType.INT)
            declaration = declarations.VariableDeclaration(
                None, ctyp, instruction.name, None, None
            )
            self.emit_statement(
                statements.DeclarationStatement(declaration, None)
            )
        elif isinstance(instruction, ir.Store):
            lhs = self.get_var_ref(instruction.address)
            value = self.get_var_ref(instruction.value)
            typ = self.get_ctype()
            expression = expressions.BinaryOperator(
                lhs, "=", value, typ, True, None
            )
            self.emit_expression(expression)
        elif isinstance(instruction, ir.Load):
            lhs = self.get_var_ref(instruction)
            address = self.get_var_ref(instruction.address)
            typ = self.get_ctype()
            rhs = expressions.UnaryOperator("*", address, typ, False, None)
            self.emit_store(lhs, rhs)
        elif isinstance(instruction, ir.Binop):
            lhs = instruction.name
            op = instruction.op
            a = instruction.a
            b = instruction.b
            typ = instruction.typ
            rhs = expressions.BinaryOperator(a, op, b, typ, False, None)
            print(lhs, rhs)
            self.emit_store(lhs, rhs)
        elif isinstance(instruction, ir.AddressOf):
            typ = self.voidptr_type
            loc = None
            src = self.get_var_ref(instruction.src)
            expression = expressions.UnaryOperator("&", src, typ, False, loc)
            self.emit_expression(expression)
        elif isinstance(instruction, ir.Cast):
            dst = self.get_var_ref(instruction)
            src = self.get_var_ref(instruction.src)
            # TODO: do some casting?
            self.emit_store(dst, src)
        elif isinstance(instruction, ir.LiteralData):
            value = instruction.data
            typ = self.voidptr_type
            loc = None
            expression = expressions.StringLiteral(value, typ, loc)
            self.emit_expression(expression)
        elif isinstance(instruction, ir.ProcedureCall):
            callee = self.get_var_ref(instruction.callee)
            args = []
            typ = self.voidptr_type
            loc = None
            call = expressions.FunctionCall(callee, args, typ, False, loc)
            self.emit_expression(call)
        elif isinstance(instruction, ir.Exit):
            self.emit_statement(statements.Return(None, None))
        elif isinstance(instruction, ir.Return):
            value = expressions.VariableAccess()
            self.emit_statement(statements.Return(value, None))
        else:  # pragma: no cover
            raise NotImplementedError(str(instruction))
