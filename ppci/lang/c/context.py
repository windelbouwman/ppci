""" A context where other parts share global state """

from ...common import CompilerError
from .types import BareType
from . import types, expressions, declarations


def type_tuple(*args):
    return tuple(sorted(args))


class CContext:
    """ A context as a substitute for global data """
    def __init__(self, coptions, arch_info):
        self.coptions = coptions
        self.arch_info = arch_info

        self.atomic_types = {
            type_tuple('void'): BareType.VOID,
            type_tuple('char',): BareType.CHAR,
            type_tuple('signed', 'char'): BareType.SCHAR,
            type_tuple('unsigned', 'char'): BareType.UCHAR,
            type_tuple('short',): BareType.SHORT,
            type_tuple('signed', 'short',): BareType.SHORT,
            type_tuple('short', 'int'): BareType.SHORT,
            type_tuple('signed', 'short', 'int'): BareType.SHORT,
            type_tuple('unsigned', 'short'): BareType.USHORT,
            type_tuple('unsigned', 'short', 'int'): BareType.USHORT,
            type_tuple('int',): BareType.INT,
            type_tuple('signed', 'int',): BareType.INT,
            type_tuple('unsigned', 'int',): BareType.UINT,
            type_tuple('unsigned',): BareType.UINT,
            type_tuple('long',): BareType.LONG,
            type_tuple('signed', 'long',): BareType.LONG,
            type_tuple('long', 'int'): BareType.LONG,
            type_tuple('signed', 'long', 'int'): BareType.LONG,
            type_tuple('unsigned', 'long'): BareType.ULONG,
            type_tuple('unsigned', 'long', 'int'): BareType.ULONG,
            type_tuple('long', 'long',): BareType.LONGLONG,
            type_tuple('signed', 'long', 'long',): BareType.LONGLONG,
            type_tuple('long', 'long', 'int'): BareType.LONGLONG,
            type_tuple('signed', 'long', 'long', 'int'):
                BareType.LONGLONG,
            type_tuple('unsigned', 'long', 'long'): BareType.ULONGLONG,
            type_tuple('unsigned', 'long', 'long', 'int'):
                BareType.ULONGLONG,
            type_tuple('float',): BareType.FLOAT,
            type_tuple('double',): BareType.DOUBLE,
            type_tuple('long', 'double'): BareType.LONGDOUBLE,
        }

        int_size = self.arch_info.get_size('int')
        self.type_size_map = {
            BareType.CHAR: 1,
            BareType.SCHAR: 1,
            BareType.UCHAR: 1,
            BareType.SHORT: 2,
            BareType.USHORT: 2,
            BareType.INT: int_size,
            BareType.UINT: int_size,
            BareType.LONG: 8,
            BareType.ULONG: 8,
            BareType.LONGLONG: 8,
            BareType.ULONGLONG: 8,
            BareType.FLOAT: 4,
            BareType.DOUBLE: 8,
            BareType.LONGDOUBLE: 10,
        }

    def is_valid(self, type_specifiers):
        """ Check if the type specifiers refer to a valid basic type """
        assert isinstance(type_specifiers, (list, tuple))
        key = type_tuple(*type_specifiers)
        return key in self.atomic_types

    def get_type(self, type_specifiers):
        """ Create a new instance for the given type specifiers """
        assert isinstance(type_specifiers, (list, tuple))
        key = type_tuple(*type_specifiers)
        a = self.atomic_types[key]
        return BareType(a)

    def equal_types(self, typ1, typ2, unqualified=False):
        """ Check for type equality """
        # TODO: enhance!
        if typ1 is typ2:
            # A short circuit:
            return True
        # elif isinstance(typ1, nodes.QualifiedType):
        #    # Handle qualified types:
        #    if isinstance(typ2, nodes.QualifiedType):
        #        return typ1.qualifiers == typ2.qualifiers and \
        #            self.equal_types(typ1.typ, typ2.typ)
        #    else:
        #        return (not typ1.qualifiers) and \
        #            self.equal_types(typ1.typ, typ2)
        elif isinstance(typ1, types.BareType):
            if isinstance(typ2, types.BareType):
                return typ1.type_id == typ2.type_id
        elif isinstance(typ1, types.FunctionType):
            if isinstance(typ2, types.FunctionType):
                return \
                    len(typ1.argument_types) == len(typ2.argument_types) and \
                    self.equal_types(typ1.return_type, typ2.return_type) and \
                    all(self.equal_types(a1, a2) for a1, a2 in zip(
                        typ1.argument_types, typ2.argument_types))
        elif isinstance(typ1, types.IndexableType):
            if isinstance(typ2, types.IndexableType):
                return self.equal_types(typ1.element_type, typ2.element_type)
        elif isinstance(typ1, types.UnionType):
            if isinstance(typ2, types.UnionType):
                return typ1 is typ2
        elif isinstance(typ1, types.StructType):
            if isinstance(typ2, types.StructType):
                return typ1 is typ2
        elif isinstance(typ1, types.EnumType):
            if isinstance(typ2, types.EnumType):
                return typ1 is typ2
        else:
            raise NotImplementedError(str(typ1))
        return False

    def deprecated_resolve_type(self, typ):
        """ Given a type, look behind the identifiertype """
        # TODO: redesign qualifiers for sure.
        return typ
        while isinstance(typ, (types.IdentifierType, types.QualifiedType)):
            typ = typ.typ

    def sizeof(self, typ: types.CType):
        """ Given a type, determine its size in whole bytes """
        assert isinstance(typ, types.CType)
        if isinstance(typ, types.ArrayType):
            element_size = self.sizeof(typ.element_type)
            if typ.size is None:
                self.error(
                    'Size of array could not be determined!', typ.location)
            assert isinstance(typ.size, int), str(type(typ.size))
            array_size = typ.size
            return element_size * array_size
        elif isinstance(typ, types.BareType):
            return self.type_size_map[typ.type_id]
        elif isinstance(typ, types.StructType):
            if not typ.complete:
                self.error('Storage size unknown', typ.location)
            # TODO: round up somewhat?
            return sum(self.sizeof(part.typ) for part in typ.fields)
        elif isinstance(typ, types.UnionType):
            if not typ.complete:
                self.error('Type is incomplete, size unknown', typ)
            return max(self.sizeof(part.typ) for part in typ.fields)
        elif isinstance(typ, types.EnumType):
            if not typ.complete:
                self.error('Storage size unknown', typ)
            # For enums take int as the type
            return self.arch_info.get_size('int')
        elif isinstance(typ, types.PointerType):
            return self.arch_info.get_size('ptr')
        elif isinstance(typ, types.FunctionType):
            # TODO: can we determine size of a function type? Should it not
            # be pointer to a function?
            return self.arch_info.get_size('ptr')
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))

    def error(self, message, location):
        """ Trigger an error at the given location """
        raise CompilerError(message, loc=location)

    def is_const_expr(self, expr):
        """ Test if an expression can be evaluated at compile time """
        if isinstance(expr, expressions.Binop):
            return self.is_const_expr(expr.a) and self.is_const_expr(expr.b)
        elif isinstance(expr, expressions.NumericLiteral):
            return True
        elif isinstance(expr, expressions.CharLiteral):
            return True
        elif isinstance(expr, expressions.Sizeof):
            return True
        else:
            return False

    def eval_expr(self, expr):
        """ Evaluate an expression right now! (=at compile time) """
        if isinstance(expr, expressions.Binop):
            lhs = self.eval_expr(expr.a)
            rhs = self.eval_expr(expr.b)
            op = expr.op

            op_map = {
                '+': lambda x, y: x + y,
                '-': lambda x, y: x - y,
                '*': lambda x, y: x * y,
            }

            # Ensure division is integer division:
            if expr.typ.is_integer:
                op_map['/'] = lambda x, y: x // y
                op_map['>>'] = lambda x, y: x >> y
                op_map['<<'] = lambda x, y: x << y
            else:
                op_map['/'] = lambda x, y: x / y

            value = op_map[op](lhs, rhs)
        elif isinstance(expr, expressions.Unop):
            if expr.op in ['-']:
                a = self.eval_expr(expr.a)
                op_map = {
                    '-': lambda x: -x,
                }
                value = op_map[expr.op](a)
            else:  # pragma: no cover
                raise NotImplementedError(str(expr))
        elif isinstance(expr, expressions.VariableAccess):
            if isinstance(expr.variable, declarations.ValueDeclaration):
                value = expr.variable.value
            else:
                raise NotImplementedError(str(expr.variable))
        elif isinstance(expr, expressions.NumericLiteral):
            value = expr.value
        elif isinstance(expr, expressions.CharLiteral):
            value = expr.value
        elif isinstance(expr, expressions.Cast):
            # TODO: do some real casting!
            value = self.eval_expr(expr.expr)
        elif isinstance(expr, expressions.Sizeof):
            value = self.sizeof(expr.sizeof_typ)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))
        return value
