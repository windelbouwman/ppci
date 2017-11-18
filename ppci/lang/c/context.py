""" A context where other parts share global state """

import struct
from ...common import CompilerError
from .types import BareType
from . import types, expressions, declarations


def type_tuple(*args):
    """ Return sorted tuple """
    return tuple(sorted(args))


class CContext:
    """ A context as a substitute for global data """
    def __init__(self, coptions, arch_info):
        self.coptions = coptions
        self.arch_info = arch_info

        self.atomic_types = {
            type_tuple('void'): BareType.VOID,
            type_tuple('char',): BareType.CHAR,
            type_tuple('signed', 'char'): BareType.CHAR,
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
        int_alignment = self.arch_info.get_alignment('int')
        ptr_size = self.arch_info.get_size('ptr')
        self.type_size_map = {
            BareType.CHAR: (1, 1),
            BareType.UCHAR: (1, 1),
            BareType.SHORT: (2, 2),
            BareType.USHORT: (2, 2),
            BareType.INT: (int_size, int_alignment),
            BareType.UINT: (int_size, int_alignment),
            BareType.LONG: (8, 8),
            BareType.ULONG: (8, 8),
            BareType.LONGLONG: (8, 8),
            BareType.ULONGLONG: (8, 8),
            BareType.FLOAT: (4, 4),
            BareType.DOUBLE: (8, 8),
            BareType.LONGDOUBLE: (10, 10),
        }

        int_map = {
            2: 'h', 4: 'i', 8: 'q'
        }

        self.ctypes_names = {
            types.BareType.CHAR: '<b',
            types.BareType.UCHAR: '<B',
            types.BareType.SHORT: '<h',
            types.BareType.USHORT: '<H',
            types.BareType.INT: '<' + int_map[int_size].lower(),
            types.BareType.UINT: '<' + int_map[int_size].upper(),
            'ptr': '<' + int_map[ptr_size].upper(),
            types.BareType.LONGLONG: '<q',
            types.BareType.ULONGLONG: '<Q',
            types.BareType.FLOAT: '<f',
            types.BareType.DOUBLE: '<d',
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
            return self.type_size_map[typ.type_id][0]
        elif isinstance(typ, types.StructType):
            if not typ.complete:
                self.error('Storage size unknown', typ.location)
            # Take offset of last field plus its size:
            last_field = typ.fields[-1]
            return last_field.offset + self.sizeof(last_field.typ)
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

    def alignment(self, typ: types.CType):
        """ Given a type, determine its alignment in bytes """
        assert isinstance(typ, types.CType)
        if isinstance(typ, types.ArrayType):
            return self.alignment(typ.element_type)
        elif isinstance(typ, types.BareType):
            return self.type_size_map[typ.type_id][1]
        elif isinstance(typ, types.StructType):
            if not typ.complete:
                self.error('Storage size unknown', typ.location)
            return max(self.alignment(part.typ) for part in typ.fields)
        elif isinstance(typ, types.UnionType):
            if not typ.complete:
                self.error('Type is incomplete, size unknown', typ)
            return max(self.alignment(part.typ) for part in typ.fields)
        elif isinstance(typ, types.EnumType):
            if not typ.complete:
                self.error('Storage size unknown', typ)
            # For enums take int as the type
            return self.arch_info.get_alignment('int')
        elif isinstance(typ, types.PointerType):
            return self.arch_info.get_alignment('ptr')
        elif isinstance(typ, types.FunctionType):
            # TODO: can we determine size of a function type? Should it not
            # be pointer to a function?
            return self.arch_info.get_alignment('ptr')
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))

    def pack(self, typ, value):
        """ Pack a type into proper memory format """
        # TODO: is the size of the integer correct? should it be 4 or 8 bytes?
        if isinstance(typ, types.PointerType):
            tid = 'ptr'
        else:
            assert isinstance(typ, types.BareType)
            tid = typ.type_id
        fmt = self.ctypes_names[tid]
        # Check format with arch options:
        assert self.sizeof(typ) == struct.calcsize(fmt)
        return struct.pack(fmt, value)

    def gen_global_ival(self, typ, ival):
        """ Create memory image for initial value of global variable """
        if isinstance(typ, types.ArrayType):
            mem = bytes()
            for iv in ival.elements:
                mem = mem + self.gen_global_ival(typ.element_type, iv)
        elif isinstance(typ, types.StructType):
            mem = bytes()
            for field, iv in zip(typ.fields, ival.elements):
                if len(mem) < field.offset:
                    padding_count = field.offset - len(mem)
                    mem = mem + bytes([0] * padding_count)
                mem = mem + self.gen_global_ival(field.typ, iv)
        elif isinstance(typ, types.UnionType):
            mem = bytes()
            # Initialize the first field!
            mem = mem + self.gen_global_ival(
                typ.fields[0].typ, ival.elements[0])
            size = self.sizeof(typ)
            filling = size - len(mem)
            assert filling >= 0
            mem = mem + bytes([0] * filling)
        elif isinstance(typ, (types.BareType, types.PointerType)):
            cval = self.eval_expr(ival)
            mem = self.pack(typ, cval)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))
        return mem

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
