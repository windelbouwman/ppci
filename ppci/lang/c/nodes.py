""" Classes for the abstract syntax tree (AST) nodes for the C language.

The goal is to be able to recreate source from this ast as close to
the original source as possible.
"""

from ..generic.nodes import Statement, Compound, Expression


class CompilationUnit:
    """ A single compilation unit """
    def __init__(self, declarations):
        self.declarations = declarations

    def __repr__(self):
        return 'Compilation unit with {} declarations'.format(
            len(self.declarations))


class DeclSpec:
    """ Contains a type and a set of modifiers """
    def __init__(self):
        self.typ = None  # The later determined type!
        self.storage_class = None
        self.type_qualifiers = set()
        self.declarators = []

    def __repr__(self):
        return '[decl-spec storage={}, qualifiers={}, type={}, {}]'.format(
            self.storage_class, self.type_qualifiers, self.typ,
            self.declarators)


class Declarator:
    def __init__(self, name, modifiers, initializer, loc):
        self.name = name
        self.modifiers = modifiers
        self.initializer = initializer
        self.loc = loc


# Type parse nodes:
class TypeNode:
    def __init__(self, location):
        self.location = location


class IdentifierType(TypeNode):
    """ A type given by a series of type specifiers """
    def __init__(self, name, location):
        super().__init__(location)
        self.name = name


class BasicType(TypeNode):
    """ Basic type specification """
    def __init__(self, type_specifiers, location):
        super().__init__(location)
        self.type_specifiers = type_specifiers

    def __repr__(self):
        return 'Basic type "{}"'.format(' '.join(self.type_specifiers))


class StructFieldDeclarator(TypeNode):
    """ A declaration of a field inside a struct or union """
    def __init__(self, name, type_modifiers, bitsize, location):
        super().__init__(location)
        self.name = name
        self.modifiers = type_modifiers
        self.bitsize = bitsize


class StructOrUnion(TypeNode):
    """ A struct or a union """
    def __init__(self, tag, fields, location):
        super().__init__(location)
        self.tag = tag
        self.fields = fields


class Struct(StructOrUnion):
    """ Struct """
    def __repr__(self):
        return 'Struct declaration'


class Union(StructOrUnion):
    """ Union """
    def __repr__(self):
        return 'Union declaration'


class Enum(TypeNode):
    """ A declaration of an enum """
    def __init__(self, tag, values, location):
        super().__init__(location)
        self.tag = tag
        self.values = values


class Enumerator(TypeNode):
    """ A single enum value """
    def __init__(self, name, value, location):
        super().__init__(location)
        self.name = name
        self.value = value

    def __repr__(self):
        return 'Enumerator: {}'.format(self.name)


# Statements:
class If(Statement):
    """ If statement """
    def __init__(self, condition, yes, no, location):
        super().__init__(location)
        self.condition = condition
        self.yes = yes
        self.no = no

    def __repr__(self):
        return 'If'


class Switch(Statement):
    """ Switch statement """
    def __init__(self, expression, statement, location):
        super().__init__(location)
        self.expression = expression
        self.statement = statement

    def __repr__(self):
        return 'Switch'


class While(Statement):
    """ While statement """
    def __init__(self, condition, body, location):
        super().__init__(location)
        self.condition = condition
        self.body = body


class DoWhile(Statement):
    """ Do-while statement """
    def __init__(self, body, condition, location):
        super().__init__(location)
        self.condition = condition
        self.body = body

    def __repr__(self):
        return 'Do-while'


class For(Statement):
    """ For statement """
    def __init__(self, init, condition, post, body, location):
        super().__init__(location)
        self.init = init
        self.condition = condition
        self.post = post
        self.body = body

    def __repr__(self):
        return 'For'


class Break(Statement):
    """ Break statement """
    def __repr__(self):
        return 'Break'


class Continue(Statement):
    """ Continue statement """
    def __repr__(self):
        return 'Continue'


class Case(Statement):
    """ Case statement """
    def __init__(self, value, statement, location):
        super().__init__(location)
        self.value = value
        self.statement = statement

    def __repr__(self):
        return 'Case'


class Default(Statement):
    """ Default statement """
    def __init__(self, statement, location):
        super().__init__(location)
        self.statement = statement

    def __repr__(self):
        return 'Default'


class Label(Statement):
    """ A label """
    def __init__(self, name, statement, location):
        super().__init__(location)
        self.name = name
        self.statement = statement

    def __repr__(self):
        return '{}:'.format(self.name)


class Goto(Statement):
    """ Goto statement """
    def __init__(self, label, location):
        super().__init__(location)
        self.label = label

    def __repr__(self):
        return 'Goto {}'.format(self.label)


class Return(Statement):
    """ Return statement """
    def __init__(self, value, location):
        super().__init__(location)
        self.value = value

    def __repr__(self):
        return 'Return'


class Empty(Statement):
    """ Do nothing! """
    def __repr__(self):
        return 'Empty'


class ExpressionStatement(Statement):
    def __init__(self, expression):
        super().__init__(expression.location)
        self.expression = expression

    def __repr__(self):
        return 'Expression statement'


class DeclarationStatement(Statement):
    def __init__(self, declaration, location):
        super().__init__(location)
        self.declaration = declaration

    def __repr__(self):
        return 'Declaration statement'


class FunctionCall(Expression):
    """ Function call """
    def __init__(self, name, args, location):
        super().__init__(location)
        self.name = name
        self.args = args

    def __repr__(self):
        return 'FunctionCall {}'.format(self.name)


class Ternop(Expression):
    """ Ternary operator """
    def __init__(self, a, op, b, c, location):
        super().__init__(location)
        assert isinstance(a, Expression)
        assert isinstance(b, Expression)
        assert isinstance(c, Expression)
        assert op == '?'
        self.a = a
        self.op = op
        self.b = b
        self.c = c

    def __repr__(self):
        return 'TernOp {}'.format(self.op)


class Binop(Expression):
    """ Binary operator """
    def __init__(self, a, op, b, location):
        super().__init__(location)
        assert isinstance(a, Expression)
        assert isinstance(b, Expression)
        self.a = a
        self.op = op
        self.b = b

    def __repr__(self):
        return 'BinaryOp {}'.format(self.op)


class Unop(Expression):
    """ Unary operator """
    def __init__(self, op, a, location):
        super().__init__(location)
        assert isinstance(a, Expression)
        self.a = a
        self.op = op

    def __repr__(self):
        return 'UnaryOp {}'.format(self.op)


class Cast(Expression):
    def __init__(self, to_typ, expr, location):
        super().__init__(location)
        self.to_typ = to_typ
        self.expr = expr

    def __repr__(self):
        return 'Cast {}'.format(self.to_typ)


class Sizeof(Expression):
    """ Sizeof operator """
    def __init__(self, sizeof_typ, location):
        super().__init__(location)
        self.sizeof_typ = sizeof_typ

    def __repr__(self):
        return 'Sizeof {}'.format(self.sizeof_typ)


class ArrayIndex(Expression):
    """ Array indexing """
    def __init__(self, base, index, location):
        super().__init__(location)
        self.base = base
        self.index = index

    def __repr__(self):
        return 'Array index'


class FieldSelect(Expression):
    """ Select a field in a struct """
    def __init__(self, base, field, location):
        super().__init__(location)
        self.base = base
        self.field = field

    def __repr__(self):
        return 'Field select'


class VariableAccess(Expression):
    def __init__(self, name, location):
        super().__init__(location)
        self.name = name

    def __repr__(self):
        return 'Id {}'.format(self.name)


class Literal(Expression):
    def __init__(self, value, location):
        super().__init__(location)
        self.value = value

    def __repr__(self):
        return 'Literal {}'.format(self.value)


class CharLiteral(Literal):
    """ A character literal """
    def __repr__(self):
        return 'Char literal {}'.format(self.value)


class NumericLiteral(Literal):
    def __repr__(self):
        return 'Numeric literal {}'.format(self.value)


class StringLiteral(Literal):
    """ A string literal """
    def __repr__(self):
        return 'String literal {}'.format(self.value)


class InitializerList(Expression):
    """ A c style initializer list """
    def __init__(self, elements, loc):
        super().__init__(loc)
        self.elements = elements

    def __repr__(self):
        return 'Initializer list'


__all__ = ['If', 'Compound']
