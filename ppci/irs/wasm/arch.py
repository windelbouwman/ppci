""" Architecture description for web assembly """

from ... import ir
from ...arch.arch import VirtualMachineArchitecture
from ...arch.stack import FramePointerLocation
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


class WasmArchitecture(VirtualMachineArchitecture):
    """ Web assembly architecture description """
    name = 'wasm'

    def __init__(self):
        super().__init__()
        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1), ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 1), ir.u16: TypeInfo(2, 1),
                ir.i32: TypeInfo(4, 1), ir.u32: TypeInfo(4, 1),
                ir.i64: TypeInfo(8, 1), ir.u64: TypeInfo(8, 1),
                'int': ir.i32, 'ptr': ir.i32
            },
            register_classes=register_classes)
        self.fp_location = FramePointerLocation.BOTTOM
