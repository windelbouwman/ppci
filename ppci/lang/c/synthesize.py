from ... import ir
from . import types, declarations, expressions, statements


class CSynthesizer:
    """ Take an IR-module and convert it into a C-AST.

    This does essentially the opposite of the codegenerator. """
    def __init__(self):
        pass

    def syn_module(self, ir_module):
        pass

    def syn_function(self, ir_function):
        pass

    def syn_block(self, block):
        """ Synthesize an ir block into C """
        for instruction in block:
            self.syn_instruction(instruction)
        compund = statements.Compund()
        statements.Label()

    def syn_instruction(self, instruction):
        """ Convert ir instruction to its corresponding C counterpart """
        if isinstance(instruction, ir.Alloc):
            pass
        elif isinstance(instruction, ir.Binop):
            lhs = instruction.name
            rhs = expressions.Binop(insutrction.a, op, instruction.b)
            expression = expressions.Binop('=', a, b, d)
            statement = statements.ExpressionStatement(expression)
        elif isinstance(instruction, ir.Exit):
            statement = statements.Return()
        elif isinstance(instruction, ir.Return):
            value = expressions.VariableAccess()
            statement = statements.Return(value)
        else:  # pragma: no cover
            raise NotImplementedError(str(instruction))
        return statement
