""" A context where other parts share global state.


"""

import logging
import struct
from ...common import CompilerError
from ...arch.arch_info import Endianness
from ... import ir
from .nodes.types import BasicType
from .nodes import types, expressions
from .utils import required_padding
from .eval import ConstantExpressionEvaluator


class CContext:
    """ A context as a substitute for global data """

    logger = logging.getLogger("ccontext")

    def __init__(self, coptions, arch_info):
        self.coptions = coptions
        self.arch_info = arch_info
        self._expression_evaluator = ConstantExpressionEvaluator(self)

        self._field_offsets = {}
        self._enum_values = {}

        # Grab integer size from arch info:
        int_size = self.arch_info.get_size("int")
        int_alignment = self.arch_info.get_alignment("int")
        long_size = self.arch_info.get_size("long")
        long_alignment = self.arch_info.get_alignment("long")

        # C requires sizeof(int) <= sizeof(long):
        long_size = max(int_size, long_size)
        long_alignment = max(int_alignment, long_alignment)
        longlong_size = max(int_size, 8)
        longlong_alignment = max(int_alignment, 8)

        ptr_size = self.arch_info.get_size("ptr")
        double_size = self.arch_info.get_size(ir.f64)
        double_alignment = self.arch_info.get_alignment(ir.f64)
        self.type_size_map = {
            BasicType.CHAR: (1, 1),
            BasicType.UCHAR: (1, 1),
            BasicType.SHORT: (2, 2),
            BasicType.USHORT: (2, 2),
            BasicType.INT: (int_size, int_alignment),
            BasicType.UINT: (int_size, int_alignment),
            BasicType.LONG: (long_size, long_alignment),
            BasicType.ULONG: (long_size, long_alignment),
            BasicType.LONGLONG: (longlong_size, longlong_alignment),
            BasicType.ULONGLONG: (longlong_size, longlong_alignment),
            BasicType.FLOAT: (4, 4),
            BasicType.DOUBLE: (double_size, double_alignment),
            BasicType.LONGDOUBLE: (10, 10),
        }

        int_map = {2: "h", 4: "i", 8: "q"}

        if self.arch_info.endianness == Endianness.LITTLE:
            byte_order = "<"
        else:
            byte_order = ">"

        if double_size == 4:
            ftype = "f"
        else:
            ftype = "d"

        ctypes = {
            BasicType.CHAR: "b",
            BasicType.UCHAR: "B",
            BasicType.SHORT: "h",
            BasicType.USHORT: "H",
            BasicType.INT: int_map[int_size].lower(),
            BasicType.UINT: int_map[int_size].upper(),
            "ptr": int_map[ptr_size].upper(),
            BasicType.LONG: int_map[long_size].lower(),
            BasicType.ULONG: int_map[long_size].upper(),
            BasicType.LONGLONG: "q",
            BasicType.ULONGLONG: "Q",
            BasicType.FLOAT: "f",
            BasicType.DOUBLE: ftype,
        }

        self.ctypes_names = {t: byte_order + v for t, v in ctypes.items()}

    def sizeof(self, typ: types.CType):
        """ Given a type, determine its size in whole bytes """
        if not isinstance(typ, types.CType):
            raise TypeError("typ should be CType: {}".format(typ))

        if isinstance(typ, types.ArrayType):
            assert typ.size is not None
            element_size = self.sizeof(typ.element_type)
            if isinstance(typ.size, int):
                array_size = typ.size
            else:
                array_size = self.eval_expr(typ.size)
            size = element_size * array_size
        elif isinstance(typ, types.BasicType):
            size = self.type_size_map[typ.type_id][0]
        elif isinstance(typ, types.StructType):
            if not typ.complete:
                self.error("Storage size unknown", typ.location)
            size = self.get_field_offsets(typ)[0]
        elif isinstance(typ, types.UnionType):
            if not typ.complete:
                self.error("Type is incomplete, size unknown", typ)
            size = max(self.sizeof(part.typ) for part in typ.fields)
        elif isinstance(typ, types.EnumType):
            if not typ.complete:
                self.error("Storage size unknown", typ)
            # For enums take int as the type
            size = self.arch_info.get_size("int")
        elif isinstance(typ, (types.PointerType, types.FunctionType)):
            size = self.arch_info.get_size("ptr")
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))
        return size

    def alignment(self, typ: types.CType):
        """ Given a type, determine its alignment in bytes """
        assert isinstance(typ, types.CType)
        if isinstance(typ, types.ArrayType):
            if typ.size is None:
                alignment = self.arch_info.get_alignment("ptr")
            else:
                alignment = self.alignment(typ.element_type)
        elif isinstance(typ, types.BasicType):
            alignment = self.type_size_map[typ.type_id][1]
        elif isinstance(typ, types.StructType):
            if not typ.complete:
                self.error("Storage size unknown", typ.location)
            alignment = max(self.alignment(part.typ) for part in typ.fields)
        elif isinstance(typ, types.UnionType):
            if not typ.complete:
                self.error("Type is incomplete, size unknown", typ)
            alignment = max(self.alignment(part.typ) for part in typ.fields)
        elif isinstance(typ, types.EnumType):
            if not typ.complete:
                self.error("Storage size unknown", typ)
            # For enums take int as the type
            alignment = self.arch_info.get_alignment("int")
        elif isinstance(typ, (types.PointerType, types.FunctionType)):
            alignment = self.arch_info.get_alignment("ptr")
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))
        return alignment

    def layout_struct(self, typ):
        """ Layout the fields in the struct.

        Things to take in account:
        - alignment
        - bit packing
        - anonynous types
        """
        kind = "struct" if isinstance(typ, types.StructType) else "union"

        bit_offsets = {}
        bit_offset = 0  # Offset in bits
        for field in typ.fields:
            # Calculate bit size:
            if field.bitsize:
                bitsize = self.eval_expr(field.bitsize)
                alignment = 1  # Bitfields are 1 bit aligned
            else:
                bitsize = self.sizeof(field.typ) * 8
                alignment = self.alignment(field.typ) * 8

            # alignment handling:
            bit_offset += required_padding(bit_offset, alignment)

            # We are now at the position of this field
            bit_offsets[field] = bit_offset

            if field.name is None:
                # If the field is anonymous, fill the offsets of named subfields:
                assert field.typ.is_struct_or_union
                _, sub_field_bit_offsets = self.layout_struct(field.typ)
                for (
                    sub_field,
                    sub_field_bit_offset,
                ) in sub_field_bit_offsets.items():
                    bit_offsets[sub_field] = bit_offset + sub_field_bit_offset

            if kind == "struct":
                bit_offset += bitsize

        # TODO: should we take care here of maximum alignment as well?
        # Finally align at 8 bits:
        bit_offset += required_padding(bit_offset, 8)
        assert bit_offset % 8 == 0
        byte_size = bit_offset // 8
        return byte_size, bit_offsets

    def get_field_offsets(self, typ):
        """ Get a dictionary with offset of fields """
        if typ not in self._field_offsets:
            size, offsets = self.layout_struct(typ)
            self._field_offsets[typ] = size, offsets
        return self._field_offsets[typ]

    def offsetof(self, typ, field):
        """ Returns the offset of a field in a struct/union in bytes """
        field_offset = self.get_field_offsets(typ)[1][field]
        # Note that below assert will not always hold.
        # It is also used to create debug types.
        # assert field_offset % 8 == 0
        return field_offset // 8

    def has_field(self, typ, field_name):
        """ Check if the given type has the given field. """
        if not typ.is_struct_or_union:
            raise TypeError("typ must be union or struct type")

        return typ.has_field(field_name)

    def get_field(self, typ, field_name):
        """ Get the given field. """
        if not typ.is_struct_or_union:
            raise TypeError("typ must be union or struct type")

        if typ.has_field(field_name):
            return typ.get_field(field_name)
        raise KeyError(field_name)

    def get_enum_value(self, enum_typ, enum_constant):
        if enum_constant not in self._enum_values:
            self._calculate_enum_values(enum_typ)
        return self._enum_values[enum_constant]

    def _calculate_enum_values(self, ctyp):
        """ Determine enum values """
        value = 0
        for constant in ctyp.constants:
            if constant.value:
                value = self.eval_expr(constant.value)
            self._enum_values[constant] = value

            # Increase for next enum value:
            value += 1

    def pack(self, typ, value):
        """ Pack a type into proper memory format """
        if isinstance(typ, types.PointerType):
            tid = "ptr"
        else:
            assert isinstance(typ, types.BasicType)
            tid = typ.type_id
        fmt = self.ctypes_names[tid]
        # Check format with arch options:
        assert self.sizeof(typ) == struct.calcsize(fmt)
        return struct.pack(fmt, value)

    def _make_ival(self, typ, ival):
        """ Try to make ival a proper initializer """
        if isinstance(ival, list):
            if isinstance(typ, types.ArrayType):
                elements = [self._make_ival(typ.element_type, i) for i in ival]
                ival = expressions.ArrayInitializer(typ, elements, None)
            elif isinstance(typ, types.StructType):
                ival2 = expressions.StructInitializer(typ, None)
                for field, value in zip(typ.fields, ival):
                    value = self._make_ival(field.typ, value)
                    ival2.values[field] = value
                ival = ival2
            else:
                raise NotImplementedError(str(typ))
        elif isinstance(ival, int):
            int_type = types.BasicType(types.BasicType.INT)
            ival = expressions.NumericLiteral(ival, int_type, None)
        return ival

    @staticmethod
    def error(message, location, hints=None):
        """ Trigger an error at the given location """
        raise CompilerError(message, loc=location, hints=hints)

    def warning(self, message, location, hints=None):
        """ Trigger a warning at the given location """
        # TODO: figure a nice way to gather warnings.
        self.logger.warning(message)
        self.logger.info("At: %s, hints: %s", location, hints)

    def eval_expr(self, expr):
        """ Evaluate an expression right now! (=at compile time) """
        return self._expression_evaluator.eval_expr(expr)
