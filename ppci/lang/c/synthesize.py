from ... import ir
from ...graph.relooper import find_structure
from .nodes import types, declarations, expressions, statements


class CSynthesizer:
    """ Take an IR-module and convert it into a C-AST.

    This does essentially the opposite of the codegenerator. """
    def __init__(self):
        self.var_map = {}
        self.block_map = {}

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
        compound = statements.Compound(inner_statements)
        statements.Label(block.name, compound, None)

    def syn_instruction(self, instruction):
        """ Convert ir instruction to its corresponding C counterpart """
        if isinstance(instruction, ir.Alloc):
            ctyp = types.BareType(types.BareType.INT)
            declaration = declarations.VariableDeclaration(
                None, ctyp, instruction.name, None, None)
            statement = statements.DeclarationStatement(declaration, None)
        elif isinstance(instruction, ir.Store):
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
            # statement = statements.ExpressionStatement(expression)
        elif isinstance(instruction, ir.Exit):
            statement = statements.Return(None, None)
        elif isinstance(instruction, ir.Return):
            value = expressions.VariableAccess()
            statement = statements.Return(value, None)
        else:  # pragma: no cover
            raise NotImplementedError(str(instruction))
        return statement
