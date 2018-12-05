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
        inner_statements = []
        for instruction in block:
            inner_statements.append(self.syn_instruction(instruction))
        loc = None
        compound = statements.Compound(inner_statements, loc)
        statements.Label(block.name, compound, None)

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

    def syn_instruction(self, instruction):
        """ Convert ir instruction to its corresponding C counterpart """
        if isinstance(instruction, ir.Alloc):
            ctyp = types.BasicType(types.BasicType.INT)
            declaration = declarations.VariableDeclaration(
                None, ctyp, instruction.name, None, None)
            statement = statements.DeclarationStatement(declaration, None)
        elif isinstance(instruction, ir.Store):
            lhs = self.get_var_ref(instruction.address)
            value = self.get_var_ref(instruction.value)
            typ = self.voidptr_type
            expression = expressions.BinaryOperator(
                lhs, '=', value, typ, True, None)
            statement = statements.ExpressionStatement(expression)
        elif isinstance(instruction, ir.Binop):
            lhs = instruction.name
            op = instruction.op
            a = instruction.a
            b = instruction.b
            typ = instruction.typ
            rhs = expressions.BinaryOperator(a, op, b, typ, False, None)
            print(lhs, rhs)
            # expression = expressions.Binop('=', a, b, d)
            statement = statements.ExpressionStatement(expression)
        elif isinstance(instruction, ir.AddressOf):
            typ = self.voidptr_type
            loc = None
            src = self.get_var_ref(instruction.src)
            expression = expressions.UnaryOperator(
                '&', src, typ, False, loc)
            statement = statements.ExpressionStatement(expression)
        elif isinstance(instruction, ir.LiteralData):
            value = instruction.data
            typ = self.voidptr_type
            loc = None
            expression = expressions.StringLiteral(value, typ, loc)
            statement = statements.ExpressionStatement(expression)
        elif isinstance(instruction, ir.ProcedureCall):
            callee = self.get_var_ref(instruction.callee)
            args = []
            typ = self.voidptr_type
            loc = None
            call = expressions.FunctionCall(
                callee, args, typ, False, loc)
            statement = statements.ExpressionStatement(call)
        elif isinstance(instruction, ir.Exit):
            statement = statements.Return(None, None)
        elif isinstance(instruction, ir.Return):
            value = expressions.VariableAccess()
            statement = statements.Return(value, None)
        else:  # pragma: no cover
            raise NotImplementedError(str(instruction))
        return statement
