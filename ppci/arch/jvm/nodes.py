""" Data structures for most java related items. """

from .enums import ConstantTag
from .opcodes import op_to_name


class MethodType:
    def __init__(self, parameter_types, return_type):
        self.parameter_types = parameter_types
        self.return_type = return_type


class BaseType:
    def __init__(self, typ):
        self.typ = typ


class ObjectType:
    def __init__(self, class_name):
        self.class_name = class_name


class ArrayType:
    def __init__(self, component_type):
        self.component_type = component_type


class ClassFile:
    def __init__(
        self,
        major_version=None,
        minor_version=None,
        constant_pool=None,
        access_flags=None,
        this_class=None,
        super_class=None,
        interfaces=None,
        fields=None,
        methods=None,
        attributes=None,
    ):
        self.major_version = major_version
        self.minor_version = minor_version
        self.constant_pool = constant_pool
        self.access_flags = access_flags
        self.this_class = this_class
        self.super_class = super_class
        self.interfaces = interfaces
        self.fields = fields
        self.methods = methods
        self.attributes = attributes

    def get_constant(self, index):
        return self.constant_pool[index]

    def get_name(self, index):
        """ Get a name given by an index. """
        constant = self.get_constant(index)
        assert constant.tag == ConstantTag.Utf8
        return constant.value


class ConstantPool:
    """ Constant pool. """

    def __init__(self):
        self._pool = [None]  # Start with a dummy at position 0.

    def __getitem__(self, key):
        return self._pool[key]

    def __len__(self):
        # TODO: strictly speaking, we could return the amount
        # of non-None objects in the pool?
        return len(self._pool)

    def append(self, constant):
        self._pool.append(constant)


class Constant:
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value

    def __repr__(self):
        return "Constant {}: {}".format(self.tag, self.value)


class MethodRef:
    def __init__(self):
        self.class_name = ""

    def __repr__(self):
        return "MethodRef({})".format(self.class_name)


class Method:
    def __init__(self, access_flags, name, descriptor, attributes):
        self.access_flags = access_flags
        self.name = name
        self.descriptor = descriptor
        self.attributes = attributes


class Attribute:
    def __init__(self, name, data):
        self.name = name
        self.data = data

    def __repr__(self):
        return "Attribute(name={}, data={})".format(self.name, self.data)


class CodeAttribute:
    def __init__(self, max_stack, max_locals, code, attributes):
        self.max_stack = max_stack
        self.max_locals = max_locals
        self.code = code
        self.attributes = attributes


class Instruction:
    """ A single java instruction. """

    def __init__(self, opcode, args):
        self.opcode = opcode
        self.mnemonic = op_to_name[opcode]
        self.args = args

    def __repr__(self):
        return "instruction(opcode={} (0x{:0X}), args={})".format(
            self.mnemonic, self.opcode, self.args
        )


class Manifest:
    pass
