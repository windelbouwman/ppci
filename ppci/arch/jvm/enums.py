""" Java class file related enums. """


import enum


class ConstantTag(enum.IntEnum):
    Utf8 = 1
    Integer = 3
    Float = 4
    Long = 5
    Double = 6
    Class = 7
    String = 8
    FieldRef = 9
    MethodRef = 10
    InterfaceMethodRef = 11
    NameAndType = 12
    MethodHandle = 15
    MethodType = 16
    InvokeDynamic = 18


class AccessFlag(enum.IntEnum):
    ACC_PUBLIC = 0x1
    ACC_PRIVATE = 0x2
    ACC_PROTECTED = 0x4
    ACC_STATIC = 0x8
    ACC_FINAL = 0x10
    ACC_SUPER = 0x20
    ACC_SYNCHRONIZED = 0x20
    ACC_BRIDGE = 0x40
    ACC_VARARGS = 0x80
    ACC_NATIVE = 0x100
    ACC_INTERFACE = 0x200
    ACC_ABSTRACT = 0x400
    ACC_STRICT = 0x800
    ACC_SYNTHETIC = 0x1000
    ACC_ANNOTATION = 0x2000
    ACC_ENUM = 0x4000
