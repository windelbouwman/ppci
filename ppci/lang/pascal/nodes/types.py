class Type:
    """ Base class of all types """

    # def __init__(self, location):
    #

    @property
    def is_array(self):
        return isinstance(self, ArrayType)

    @property
    def is_record(self):
        return isinstance(self, RecordType)

    @property
    def is_pointer(self):
        return isinstance(self, PointerType)

    @property
    def is_integer(self):
        return isinstance(self, IntegerType)

    @property
    def is_real(self):
        return isinstance(self, FloatType)

    @property
    def is_enum(self):
        return isinstance(self, EnumType)

    @property
    def is_subrange(self):
        return isinstance(self, SubRange)

    @property
    def is_set(self):
        return isinstance(self, SetType)

    @property
    def is_file(self):
        return isinstance(self, FileType)

    @property
    def is_function(self):
        return isinstance(self, FunctionType)

    @property
    def is_procedure(self):
        return isinstance(self, ProcedureType)


class BaseType(Type):
    """ Built in type """

    def __init__(self, byte_size):
        super().__init__()
        self.byte_size = byte_size

    def __repr__(self):
        return "base type size={}".format(self.byte_size)


class IntegerType(BaseType):
    """ Integer base type """

    def __init__(self, byte_size):
        super().__init__(byte_size)
        self.bits = byte_size * 8


class UnsignedIntegerType(IntegerType):
    pass


class SignedIntegerType(IntegerType):
    pass


class SubRange(IntegerType):
    """ integer that can fit values in the given range. """

    def __init__(self, lower, upper, location):
        super().__init__(4)
        self.lower = lower
        self.upper = upper
        self.location = location

    def __repr__(self):
        return "sub-range({}..{})".format(self.lower, self.upper)


class FloatType(BaseType):
    """ Floating point base type """

    def __init__(self, name, byte_size, fraction_bits):
        super().__init__(name, byte_size)
        self.bits = byte_size * 8
        self.fraction_bits = fraction_bits


class EnumType(Type):
    def __init__(self, values, location):
        super().__init__()
        # TODO?
        self.values = values
        self.location = location

    def __repr__(self):
        return "enum"


class FunctionType(Type):
    """ Function blueprint, defines argument types and return type """

    def __init__(self, parameter_types, return_type):
        super().__init__()
        self.parameter_types = parameter_types
        self.return_type = return_type

    def __repr__(self):
        if self.parameter_types:
            params = "({})".format(
                ", ".join([str(v) for v in self.parameter_types])
            )
        else:
            params = ""
        return "function-type{}: {}".format(params, self.return_type)


class ProcedureType(Type):
    def __init__(self, parameter_types):
        super().__init__()
        self.parameter_types = parameter_types

    def __repr__(self):
        if self.parameter_types:
            params = "({})".format(
                ", ".join([str(v) for v in self.parameter_types])
            )
        else:
            params = ""
        return "procedure-type{}".format(params)


class PointerType(Type):
    """ A type that points to data of some other type """

    def __init__(self, ptype):
        super().__init__()
        assert isinstance(ptype, Type)
        # or isinstance(ptype, Expression)
        self.ptype = ptype

    def __repr__(self):
        return "({}*)".format(self.ptype)


class RecordField:
    """ Field of a record type """

    def __init__(self, name, typ, location):
        assert isinstance(name, str)
        self.name = name
        self.typ = typ
        self.location = location

    def __repr__(self):
        return "Member {}".format(self.name)


class RecordVariant:
    def __init__(self, tag_field, field_type, variants, location):
        self.name = tag_field
        self.typ = field_type
        self.variants = variants
        self.location = location

    def __repr__(self):
        return "Variant record member {}".format(self.name)

    def has_field(self, name: str):
        for _, fields in self.variants:
            for field in fields:
                if field.name == name:
                    return True

    def find_field(self, name):
        for _, fields in self.variants:
            for field in fields:
                if field.name == name:
                    return field


class RecordType(Type):
    """ Struct type consisting of several named members """

    def __init__(self, fields, location):
        super().__init__()
        self.fields = fields
        self.location = location
        # assert all(isinstance(field, RecordField) for field in fields)

    def has_field(self, name):
        """ Check if the struct type has a member with name """
        for field in self.fields:
            if name == field.name:
                return True
            if isinstance(field, RecordVariant):
                if field.has_field(name):
                    return True
        return False

    def field_type(self, name):
        """ Get the field type of field name """
        return self.find_field(name).typ

    def field_offset(self, name):
        """ Determine the offset of the field in the record """
        return self.find_field(name).offset

    def find_field(self, name):
        """ Looks up a field in the record type """
        for field in self.fields:
            if name == field.name:
                return field
            if isinstance(field, RecordVariant):
                if field.has_field(name):
                    return field.find_field(name)

        raise KeyError(name)  # pragma: no cover

    def __repr__(self):
        return "RECORD"


class ArrayType(Type):
    """ Array type """

    def __init__(self, element_type, dimensions, packed, location):
        super().__init__()
        self.element_type = element_type
        self.dimensions = dimensions
        self.packed = packed
        self.location = location

    def __repr__(self):
        return "ARRAY {} of {}".format(self.dimensions, self.element_type)

    def indexed(self, count):
        """ Return the resulting time when indexing this array count times.
        """
        if count > len(self.dimensions):
            raise ValueError(
                "Cannot index type more than the amount of dimensions."
            )
        elif count < len(self.dimensions):
            return ArrayType(
                self.element_type,
                self.dimensions[count:],
                self.packed,
                self.location,
            )
        else:
            assert count == len(self.dimensions)
            return self.element_type


class SetType(Type):
    """ Set type. """

    def __init__(self, element_type, location):
        super().__init__()
        self.element_type = element_type
        self.location = location


class FileType(PointerType):
    def __init__(self, component_type, location):
        super().__init__(component_type)
        # self.component_type = component_type
        self.location = location
