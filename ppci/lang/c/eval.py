from .nodes import types, expressions, declarations


class ConstantExpressionEvaluator:
    """ Class which is capable of evaluating expressions. """

    def __init__(self, context):
        self.context = context

    def eval_expr(self, expr):
        """ Evaluate an expression right now! (=at compile time) """
        if isinstance(expr, expressions.BinaryOperator):
            value = self.eval_binop(expr)
        elif isinstance(expr, expressions.UnaryOperator):
            value = self.eval_unop(expr)
        elif isinstance(expr, expressions.VariableAccess):
            value = self.eval_variable_access(expr)
        elif isinstance(expr, expressions.NumericLiteral):
            value = expr.value
        elif isinstance(expr, expressions.CharLiteral):
            value = expr.value
        elif isinstance(expr, expressions.StringLiteral):
            value = self.eval_string_literal(expr)
        elif isinstance(expr, expressions.CompoundLiteral):
            value = self.eval_compound_literal(expr)
        elif isinstance(expr, expressions.Cast):
            value = self.eval_cast(expr)
        elif isinstance(expr, expressions.Sizeof):
            if isinstance(expr.sizeof_typ, types.CType):
                value = self.context.sizeof(expr.sizeof_typ)
            else:
                value = self.context.sizeof(expr.sizeof_typ.typ)
        elif isinstance(expr, int):
            value = expr
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))
        return value

    def eval_variable_access(self, expr):
        """ Evaluate variable access. """
        declaration = expr.variable.declaration
        if isinstance(declaration, declarations.EnumConstantDeclaration):
            value = self.eval_enum(declaration)
        elif isinstance(
            declaration,
            (
                declarations.VariableDeclaration,
                declarations.FunctionDeclaration,
            ),
        ):
            value = self.eval_global_access(declaration)
        else:
            raise NotImplementedError(str(expr.variable))
        return value

    def eval_enum(self, declaration):
        """ Evaluate enum value. """
        value = self.context.get_enum_value(declaration.typ, declaration)
        return value

    def eval_global_access(self, declaration):
        raise NotImplementedError()

    def eval_string_literal(self, expr):
        raise NotImplementedError()

    def eval_compound_literal(self, expr):
        raise NotImplementedError()

    def eval_cast(self, expr):
        """ Evaluate cast expression. """
        value = self.eval_expr(expr.expr)

        # do some real casting:
        if expr.typ.is_integer:
            value = int(value)
        elif expr.typ.is_float or expr.typ.is_double:
            value = float(value)
        else:
            pass
        return value

    def eval_unop(self, expr):
        """ Evaluate unary operation. """
        if expr.op in ["-"]:
            a = self.eval_expr(expr.a)
            op_map = {"-": lambda x: -x}
            value = op_map[expr.op](a)
        elif expr.op == "&":
            value = self.eval_take_address(expr.a)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))
        return value

    def eval_take_address(self, expr):
        raise NotImplementedError("take address operator: &")

    def eval_binop(self, expr):
        """ Evaluate binary operator. """
        lhs = self.eval_expr(expr.a)
        rhs = self.eval_expr(expr.b)
        op = expr.op

        op_map = {
            "+": lambda x, y: x + y,
            "-": lambda x, y: x - y,
            "*": lambda x, y: x * y,
        }

        # Ensure division is integer division:
        if expr.typ.is_integer:
            op_map["/"] = lambda x, y: x // y
            op_map[">>"] = lambda x, y: x >> y
            op_map["<<"] = lambda x, y: x << y
        else:
            op_map["/"] = lambda x, y: x / y

        value = op_map[op](lhs, rhs)
        return value
