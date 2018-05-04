""" A context where other parts share global state.


"""

import struct
from ...common import CompilerError
from ...arch.arch_info import Endianness
from .nodes.types import BasicType
from .nodes import types, expressions, declarations
from .utils import required_padding


class CContext:
    """ A context as a substitute for global data """
    def __init__(self, coptions, arch_info):
        self.coptions = coptions
        self.arch_info = arch_info

        self._field_offsets = {}
        int_size = self.arch_info.get_size('int')
        int_alignment = self.arch_info.get_alignment('int')
        ptr_size = self.arch_info.get_size('ptr')
        self.type_size_map = {
            BasicType.CHAR: (1, 1),
            BasicType.UCHAR: (1, 1),
            BasicType.SHORT: (2, 2),
            BasicType.USHORT: (2, 2),
            BasicType.INT: (int_size, int_alignment),
            BasicType.UINT: (int_size, int_alignment),
            BasicType.LONG: (8, 8),
            BasicType.ULONG: (8, 8),
            BasicType.LONGLONG: (8, 8),
            BasicType.ULONGLONG: (8, 8),
            BasicType.FLOAT: (4, 4),
            BasicType.DOUBLE: (8, 8),
            BasicType.LONGDOUBLE: (10, 10),
        }

        int_map = {
            2: 'h', 4: 'i', 8: 'q'
        }

        if self.arch_info.endianness == Endianness.LITTLE:
            byte_order = '<'
        else:
            byte_order = '>'

        ctypes = {
            BasicType.CHAR: 'b',
            BasicType.UCHAR: 'B',
            BasicType.SHORT: 'h',
            BasicType.USHORT: 'H',
            BasicType.INT: int_map[int_size].lower(),
            BasicType.UINT: int_map[int_size].upper(),
            'ptr': int_map[ptr_size].upper(),
            BasicType.LONGLONG: 'q',
            BasicType.ULONGLONG: 'Q',
            BasicType.FLOAT: 'f',
            BasicType.DOUBLE: 'd',
        }

        self.ctypes_names = {t: byte_order + v for t, v in ctypes.items()}

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
        elif isinstance(typ1, BasicType):
            if isinstance(typ2, BasicType):
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
        if not isinstance(typ, types.CType):
            raise TypeError('typ should be CType: {}'.format(typ))

        if isinstance(typ, types.ArrayType):
            element_size = self.sizeof(typ.element_type)
            if typ.size is None:
                self.error(
                    'Size of array could not be determined!', typ.location)
            if isinstance(typ.size, int):
                array_size = typ.size
            else:
                array_size = self.eval_expr(typ.size)
            return element_size * array_size
        elif isinstance(typ, types.BasicType):
            return self.type_size_map[typ.type_id][0]
        elif isinstance(typ, types.StructType):
            if not typ.complete:
                self.error('Storage size unknown', typ.location)
            return self._get_field_offsets(typ)[0]
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
        elif isinstance(typ, types.BasicType):
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

    def layout_struct(self, kind, fields):
        """ Layout the fields in the struct: """
        offsets = {}
        offset = 0
        for field in fields:
            field_size = self.sizeof(field.typ)

            # Calculate bit size:
            if field.bitsize:
                bitsize = self.eval_expr(field.bitsize)
            else:
                bitsize = self.sizeof(field.typ) * 8

            # alignment handling:
            alignment = self.alignment(field.typ)
            offset += required_padding(offset, alignment)

            offsets[field] = offset
            if kind == 'struct':
                offset += field_size
        return offset, offsets

    def _get_field_offsets(self, typ):
        """ Get a dictionary with offset of fields """
        if typ not in self._field_offsets:
            kind = 'struct' if isinstance(typ, types.StructType) else 'union'
            size, offsets = self.layout_struct(kind, typ.fields)
            self._field_offsets[typ] = size, offsets
        return self._field_offsets[typ]

    def offsetof(self, typ, field):
        """ Returns the offset of a field in a struct/union in bytes """
        field_offset = self._get_field_offsets(typ)[1][field]
        return field_offset

    def pack(self, typ, value):
        """ Pack a type into proper memory format """
        # TODO: is the size of the integer correct? should it be 4 or 8 bytes?
        if isinstance(typ, types.PointerType):
            tid = 'ptr'
        else:
            assert isinstance(typ, types.BasicType)
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
            field_offsets = self._get_field_offsets(typ)[1]
            for field, iv in zip(typ.fields, ival.elements):
                field_offset = field_offsets[field]
                if len(mem) < field_offset:
                    padding_count = field_offset - len(mem)
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
        elif isinstance(typ, (types.BasicType, types.PointerType)):
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
        if isinstance(expr, expressions.BinaryOperator):
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
        if isinstance(expr, expressions.BinaryOperator):
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
        elif isinstance(expr, expressions.UnaryOperator):
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
            if isinstance(expr.sizeof_typ, types.CType):
                value = self.sizeof(expr.sizeof_typ)
            else:
                value = self.sizeof(expr.sizeof_typ.typ)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))
        return value
