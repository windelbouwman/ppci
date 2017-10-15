""" Architecture description for web assembly """

from ... import ir
from ...arch.arch import Architecture
from ...arch.registers import Register, RegisterClass
from ...arch.arch_info import ArchInfo, TypeInfo


# Define 'registers' that are actually wasm local variables:
class I32Register(Register):
    bitsize = 32


class I64Register(Register):
    bitsize = 64


class F32Register(Register):
    bitsize = 32


class F64Register(Register):
    bitsize = 64


register_classes = [
    RegisterClass(
        'i32',
        [ir.i8, ir.u8, ir.i16, ir.u16, ir.i32, ir.u32, ir.ptr],
        I32Register, None),
    RegisterClass(
        'i64', [ir.i64],
        I64Register, None),
    RegisterClass(
        'f32', [ir.f32],
        F32Register, None),
    RegisterClass(
        'f64', [ir.f64],
        F64Register, None),
]


class WasmArchitecture(Architecture):
    """ Web assembly architecture description """
    def __init__(self):
        super().__init__(register_classes=register_classes)
        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1), ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 1), ir.u16: TypeInfo(2, 1),
                ir.i32: TypeInfo(4, 1), ir.u32: TypeInfo(4, 1),
                ir.i64: TypeInfo(8, 1), ir.u64: TypeInfo(8, 1),
                'int': ir.i32, 'ptr': ir.i32
            })

    # TODO: get rid of below:
    # The wasm VM does not need all the functions below:
    def gen_prologue(self, frame):  # pragma: no cover
        pass
    def gen_epilogue(self, frame):  # pragma: no cover
        pass
    def gen_call(self, label, args, rv):  # pragma: no cover
        pass
    def gen_function_enter(self, args):  # pragma: no cover
        pass
    def gen_function_exit(self, rv):  # pragma: no cover
        pass
    def determine_arg_locations(self, arg_types):  # pragma: no cover
        pass
    def determine_rv_location(self, ret_type):  # pragma: no cover
        pass
    def get_compiler_rt_lib(self):
        pass
