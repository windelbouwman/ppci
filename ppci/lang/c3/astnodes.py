"""
AST (abstract syntax tree) nodes for the c3 language.
The tree is build by the parser.
Then it is checked
Finally code is generated from it.
"""

# pylint: disable=R0903


class Node:
    """ Base class of all nodes in a AST """
    pass


# Variables, parameters, local variables, constants and named types:
class Symbol(Node):
    """ Symbol is the base class for all named things like variables,
        functions, constants and types and modules """
    def __init__(self, name, public):
        self.name = name
        self.public = public


# Modules
class Module(Symbol):
    """ A module contains functions, types, consts and global variables """
    def __init__(self, name, inner_scope, loc):
        super().__init__(name, True)
        self.loc = loc
        self.imports = []
        self.inner_scope = inner_scope

    @property
    def types(self):
        """ Get the types in this module """
        return self.inner_scope.types

    @property
    def constants(self):
        """ Get the constants in this module """
        return self.inner_scope.constants

    @property
    def variables(self):
        """ Get the variables in this module """
        return self.inner_scope.variables

    @property
    def functions(self):
        """ Get all the functions that are defined in this module """
        return self.inner_scope.functions

    def __repr__(self):
        return 'MODULE {}'.format(self.name)


class Type(Node):
    """ Base class of all types """
    pass


class NamedType(Type, Symbol):
    """ Some types are named, for example a user defined type (typedef)
        and built in types. That is why this class derives from both Type
        and Symbol. """
    def __init__(self, name, public):
        super().__init__(name, public)


class BaseType(NamedType):
    """ Built in type """
    def __init__(self, name, byte_size):
        super().__init__(name, True)
        self.byte_size = byte_size

    def __repr__(self):
        return '{}'.format(self.name)


class IntegerType(BaseType):
    """ Integer base type """
    def __init__(self, name, byte_size):
        super().__init__(name, byte_size)
        self.bits = byte_size * 8


class UnsignedIntegerType(IntegerType):
    pass


class SignedIntegerType(IntegerType):
    pass


class FloatType(BaseType):
    """ Floating point base type """
    def __init__(self, name, byte_size, fraction_bits):
        super().__init__(name, byte_size)
        self.bits = byte_size * 8
        self.fraction_bits = fraction_bits


class EnumType:
    # TODO
    pass


class FunctionType(Type):
    """ Function blueprint, defines argument types and return type """
    def __init__(self, parametertypes, returntype):
        self.parametertypes = parametertypes
        self.returntype = returntype

    def __repr__(self):
        params = ', '.join([str(v) for v in self.parametertypes])
        return '{1} f({0})'.format(params, self.returntype)


class PointerType(Type):
    """ A type that points to data of some other type """
    def __init__(self, ptype):
        assert isinstance(ptype, Type) or isinstance(ptype, Expression)
        self.ptype = ptype

    def __repr__(self):
        return '({}*)'.format(self.ptype)


class StructField:
    """ Field of a struct type """
    def __init__(self, name, typ):
        assert isinstance(name, str)
        self.name = name
        self.typ = typ

    def __repr__(self):
        return 'Member {}'.format(self.name)


class StructureType(Type):
    """ Struct type consisting of several named members """
    def __init__(self, fields):
        self.fields = fields
        assert all(isinstance(mem, StructField) for mem in fields)

    def has_field(self, name):
        """ Check if the struct type has a member with name """
        for mem in self.fields:
            if name == mem.name:
                return True
        return False

    def field_type(self, name):
        """ Get the field type of field name """
        return self.find_field(name).typ

    def field_offset(self, name):
        """ Determine the offset of the field in the struct """
        return self.find_field(name).offset

    def find_field(self, name):
        """ Looks up a field in the struct type """
        for mem in self.fields:
            if name == mem.name:
                return mem
        raise KeyError(name)  # pragma: no cover

    def __repr__(self):
        return 'STRUCT'


class ArrayType(Type):
    """ Array type """
    def __init__(self, element_type, size):
        self.element_type = element_type
        self.size = size

    def __repr__(self):
        return 'ARRAY {}'.format(self.size)


class DefinedType(NamedType):
    """ A named type indicating another type """
    def __init__(self, name, typ, public, loc):
        assert isinstance(name, str)
        super().__init__(name, public)
        self.typ = typ
        self.loc = loc

    def __repr__(self):
        return '"{0}" -> "{1}"'.format(self.name, self.typ)


class Constant(Symbol):
    """ Constant definition """
    def __init__(self, name, typ, value, loc):
        super().__init__(name, True)
        self.typ = typ
        self.value = value
        self.loc = loc

    def __repr__(self):
        return 'CONSTANT {0} = {1}'.format(self.name, self.value)


class Variable(Symbol):
    """ A variable, either global or local """
    def __init__(self, name, typ, public, loc):
        super().__init__(name, public)
        self.typ = typ
        self.isLocal = False
        self.isParameter = False
        self.loc = loc
        self.ival = None

    def __repr__(self):
        return 'Var {} [{}]'.format(self.name, self.typ)


class FormalParameter(Variable):
    def __init__(self, name, typ, loc):
        super().__init__(name, typ, True, loc)
        self.isParameter = True


# Procedure types
class Function(Symbol):
    """ Actual implementation of a function """
    def __init__(self, name, public, loc):
        super().__init__(name, public)
        self.loc = loc

    def __repr__(self):
        return 'Func {}'.format(self.name)


# Operations / Expressions:
class Expression(Node):
    """ Expression base class """
    is_bool = False

    def __init__(self, loc):
        self.loc = loc


class Sizeof(Expression):
    """ Sizeof built-in contraption """
    def __init__(self, typ, loc):
        super().__init__(loc)
        self.query_typ = typ


class Deref(Expression):
    """ Data pointer dereference """
    def __init__(self, ptr, loc):
        super().__init__(loc)
        assert isinstance(ptr, Expression)
        self.ptr = ptr

    def __repr__(self):
        return 'DEREF {}'.format(self.ptr)


class TypeCast(Expression):
    """ Type cast expression to another type """
    def __init__(self, to_type, x, loc):
        super().__init__(loc)
        self.to_type = to_type
        self.a = x

    def __repr__(self):
        return 'TYPECAST {}'.format(self.to_type)


class Member(Expression):
    """ Field reference of some object, can also be package selection """
    def __init__(self, base, field, loc):
        super().__init__(loc)
        assert isinstance(base, Expression)
        assert isinstance(field, str)
        self.base = base
        self.field = field

    def __repr__(self):
        return '{}.{}'.format(self.base, self.field)


class Index(Expression):
    """ Index something, for example an array """
    def __init__(self, base, i, loc):
        super().__init__(loc)
        self.base = base
        self.i = i

    def __repr__(self):
        return 'Index {}'.format(self.i)


class Unop(Expression):
    """ Operation on one operand, typically 'op' 'expr' """
    arithmatic_ops = ('+', '-')
    logical_ops = ('not',)
    pointer_ops = ('&', '*')
    cond_ops = logical_ops
    all_ops = cond_ops + pointer_ops + arithmatic_ops

    def __init__(self, op, a, loc):
        super().__init__(loc)
        assert isinstance(a, Expression)
        assert isinstance(op, str)
        assert op in self.all_ops
        self.a = a
        self.op = op

    def __repr__(self):
        return 'UNOP {}'.format(self.op)

    @property
    def is_bool(self):
        """ Test if this binop is a boolean """
        return self.op in self.cond_ops


class Binop(Expression):
    """ Expression taking two operands and one operator """
    arithmatic_ops = ('+', '-', '*', '/', '%', '>>', '<<', '&', '|', '^')
    logical_ops = ('and', 'or')
    compare_ops = ('==', '!=', '<', '>', '<=', '>=')
    cond_ops = logical_ops + compare_ops
    all_ops = arithmatic_ops + cond_ops

    def __init__(self, a, op, b, loc):
        super().__init__(loc)
        assert isinstance(a, Expression), type(a)
        assert isinstance(b, Expression)
        assert isinstance(op, str)
        assert op in self.all_ops
        self.a = a
        self.b = b
        self.op = op   # Operation: '+', '-', '*', '/', 'mod'

    def __repr__(self):
        return 'BINOP {}'.format(self.op)

    @property
    def is_bool(self):
        """ Test if this binop is a boolean """
        return self.op in self.cond_ops


class Identifier(Expression):
    """ Reference to some identifier, can be anything from package, variable
        function or type, any named thing! """
    def __init__(self, target, scope, loc):
        super().__init__(loc)
        self.scope = scope
        self.target = target

    def __repr__(self):
        return 'ID {}'.format(self.target)


class Literal(Expression):
    """ Constant value or string """
    def __init__(self, val, loc):
        super().__init__(loc)
        self.val = val

    def __repr__(self):
        return 'LITERAL {}'.format(self.val)


class ExpressionList(Expression):
    """ List of expressions """
    def __init__(self, expressions, loc):
        super().__init__(loc)
        self.expressions = expressions

    def __repr__(self):
        return 'List [{}]'.format(self.expressions)


class NamedExpressionList(Expression):
    """ List of named expressions """
    def __init__(self, expressions, loc):
        super().__init__(loc)
        self.expressions = expressions

    def __repr__(self):
        return 'NamedList [{}]'.format(self.expressions)


class FunctionCall(Expression):
    """ Call to a some function """
    def __init__(self, proc, args, loc):
        super().__init__(loc)
        self.proc = proc
        self.args = args

    def __repr__(self):
        return 'CALL {0} '.format(self.proc)


# Statements
class Statement(Node):
    """ Base class of all statements """
    def __init__(self, loc):
        self.loc = loc


class Empty(Statement):
    """ Empty statement which does nothing! """
    def __init__(self):
        super().__init__(None)

    def __repr__(self):
        return 'NOP'


class Compound(Statement):
    """ Statement consisting of a sequence of other statements """
    def __init__(self, statements):
        super().__init__(None)
        self.statements = statements
        assert all(isinstance(s, Statement) for s in self.statements)

    def __repr__(self):
        return 'COMPOUND STATEMENT'


class Return(Statement):
    """ Return statement """
    def __init__(self, expr, loc):
        super().__init__(loc)
        self.expr = expr

    def __repr__(self):
        return 'RETURN STATEMENT'


class Assignment(Statement):
    """ Assignment statement with a left hand side and right hand side """
    operators = ('=', '|=', '&=', '+=', '-=', '*=')

    def __init__(self, lval, rval, loc, operator='='):
        super().__init__(loc)
        assert operator in self.operators
        assert isinstance(lval, Expression)
        assert isinstance(rval, Expression)
        self.lval = lval
        self.rval = rval
        self.operator = operator

    def __repr__(self):
        return 'ASSIGNMENT'

    @property
    def is_shorthand(self):
        """ Determine whether this assignment is a short hand like '+=' """
        return len(self.operator) > 1

    @property
    def shorthand_operator(self):
        """ Get the operator from '-=' to '-' """
        return self.operator[:-1]


class VariableDeclaration(Statement):
    """ A declaration of a local variable """
    def __init__(self, var, loc):
        super().__init__(loc)
        self.var = var


class ExpressionStatement(Statement):
    """ When an expression is used as a statement """
    def __init__(self, ex, loc):
        super().__init__(loc)
        self.ex = ex

    def __repr__(self):
        return 'Epression'


class If(Statement):
    """ If statement """
    def __init__(self, condition, truestatement, falsestatement, loc):
        super().__init__(loc)
        self.condition = condition
        self.truestatement = truestatement
        self.falsestatement = falsestatement

    def __repr__(self):
        return 'IF-statement'


class Switch(Statement):
    """ Switch statement """
    def __init__(self, expression, options, loc):
        super().__init__(loc)
        self.expression = expression
        self.options = options

    def __repr__(self):
        return 'SWITCH-statement'


class While(Statement):
    """ While statement """
    def __init__(self, condition, statement, loc):
        super().__init__(loc)
        self.condition = condition
        self.statement = statement

    def __repr__(self):
        return 'WHILE-statement'


class For(Statement):
    """ For statement with a start, condition and final statement """
    def __init__(self, init, condition, final, statement, loc):
        super().__init__(loc)
        self.init = init
        self.condition = condition
        self.final = final
        self.statement = statement

    def __repr__(self):
        return 'FOR-statement'
