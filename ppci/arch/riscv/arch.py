""" RISC-V architecture. """

import io
from ..arch import Architecture
from ..arch_info import ArchInfo, TypeInfo
from ..generic_instructions import Label, RegisterUseDef
from ..data_instructions import DByte, DZero
from .asm_printer import RiscvAsmPrinter
from .instructions import isa, Align, Section
from .rvc_instructions import rvcisa
from .registers import RiscvRegister, gdb_registers, Register
from .registers import R0, LR, SP, FP
from .registers import R10, R11, R12
from .registers import R13, R14, R15, R16, R17
from .registers import PC
from .registers import R9, R18, R19
from .registers import R20, R21, R22, R23, R24, R25, R26, R27
from ... import ir
from ..registers import RegisterClass
from ..stack import StackLocation
from ..stack import FramePointerLocation 
from ..data_instructions import data_isa
from ...binutils.assembler import BaseAssembler
from .instructions import dcd, Addi, Movr, Bl, Sw, Lw, Blr, Lb, Sb
from .rvc_instructions import CSwsp, CLwsp, CBl, CJr, CBlr, CMovr
from .rvc_instructions import CLwsp, CSwsp, CAddi16sp, CAddi4spn

def isinsrange(bits, val):
        msb = 1<<(bits-1)
        ll = -msb
        if (val<=(msb-1) and (val >=ll)):
            return True
        else:    
            return False


class RiscvAssembler(BaseAssembler):
    def __init__(self):
        super().__init__()
        self.lit_pool = []
        self.lit_counter = 0

    def flush(self):
        if self.in_macro:
            raise Exception()
        while self.lit_pool:
            i = self.lit_pool.pop(0)
            self.emit(i)

    def add_literal(self, v):
        """ For use in the pseudo instruction LDR r0, =SOMESYM """
        # Invent some label for the literal and store it.
        assert type(v) is str
        self.lit_counter += 1
        label_name = "_lit_{}".format(self.lit_counter)
        self.lit_pool.append(Label(label_name))
        self.lit_pool.append(dcd(v))
        return label_name


class RiscvArch(Architecture):
    name = 'riscv'
    option_names = ('rvc',)

    def __init__(self, options=None):
        super().__init__(options=options)
        if self.has_option('rvc'):
            self.isa = isa + rvcisa + data_isa
            self.store = CSwsp
            self.load = CLwsp
        else:
            self.isa = isa + data_isa
            self.store = Sw
            self.load = Lw
        self.fp_location = FramePointerLocation.BOTTOM 
        self.isa.sectinst = Section
        self.isa.dbinst = DByte
        self.isa.dsinst = DZero
        self.gdb_registers = gdb_registers
        self.gdb_pc = PC
        self.asm_printer = RiscvAsmPrinter()
        self.assembler = RiscvAssembler()
        self.assembler.gen_asm_parser(self.isa)

        # Allocatable registers:
        register_classes = [
            RegisterClass(
                'reg', [ir.i8, ir.i16, ir.i32, ir.ptr, ir.u8, ir.u16, ir.u32, ir.f32, ir.f64],
                RiscvRegister,
                [
                    R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20,
                    R21, R22, R23, R24, R25, R26, R27
                ])
        ]

        self.info = ArchInfo(
            type_infos={
                ir.i8: TypeInfo(1, 1), ir.u8: TypeInfo(1, 1),
                ir.i16: TypeInfo(2, 2), ir.u16: TypeInfo(2, 2),
                ir.i32: TypeInfo(4, 4), ir.u32: TypeInfo(4, 4),
                ir.f32: TypeInfo(4, 4), ir.f64: TypeInfo(4, 4),
                'int': ir.i32, 'ptr': ir.u32, ir.ptr: ir.u32,
            }, register_classes=register_classes)

        self.fp = FP
        self.callee_save = (
            R9, R18, R19, R20, R21, R22, R23, R24, R25, R26, R27)
        self.caller_save = (R10, R11, R12, R13, R14, R15, R16, R17)
        # (LR, FP, R9, R18, R19, R20, R21 ,R22, R23 ,R24, R25, R26, R27)

    def branch(self, reg, lab):
        if self.has_option('rvc'):
            if isinstance(lab, RiscvRegister):
                return CBlr(reg, lab, 0, clobbers=self.caller_save)
            else:
                return CBl(reg, lab, clobbers=self.caller_save)
        else:
            if isinstance(lab, RiscvRegister):
                return Blr(reg, lab, 0, clobbers=self.caller_save)
            else:
                return Bl(reg, lab, clobbers=self.caller_save)

    def get_runtime(self):
        """ Implement compiler runtime functions """
        from ...api import asm
        asm_src = """
        __sdiv:
        ; Divide x12 by x13
        ; x14 is a work register.
        ; x10 is the quotient

        mv x10, x0     ; Initialize the result
        li x14, 1      ; mov divisor into temporary register.

        ; Blow up part: blow up divisor until it is larger than the divident.
        __shiftl:
        bge x13, x12, __cont1
        slli x13, x13, 1
        slli x14, x14, 1
        j __shiftl

        ; Repeatedly substract shifted versions of divisor
        __cont1:
        beq x14, x0, __exit
        blt x12, x13, __skip
        sub x12, x12, x13
        or x10, x10, x14
        __skip:
        srli x13, x13, 1
        srli x14, x14, 1
        j __cont1

        __exit:
        jalr x0,ra,0
        """
        return asm(io.StringIO(asm_src), self)

    def move(self, dst, src):
        """ Generate a move from src to dst """
        if self.has_option('rvc'):
            return CMovr(dst, src, ismove=True)
        else:
            return Movr(dst, src, ismove=True)

    def gen_riscv_memcpy(self, dst, src, tmp, size):
        # Called before register allocation
        # Major crappy memcpy, can be improved!
        for idx in range(size):
            yield Lb(tmp, idx, src)
            yield Sb(tmp, idx, dst)

    def gen_call(self, frame, label, args, rv):
        """ Implement actual call and save / restore live registers """
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        # Setup parameters:
        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, RiscvRegister):
                yield self.move(arg_loc, arg)
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

        arg_regs = set(l for l in arg_locs if isinstance(l, Register))
        yield RegisterUseDef(uses=arg_regs)

        yield self.branch(LR, label)

        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield RegisterUseDef(defs=(retval_loc,))
            yield self.move(rv[1], retval_loc)

    def gen_function_enter(self, args):
        arg_types = [a[0] for a in args]
        arg_locs = self.determine_arg_locations(arg_types)

        arg_regs = set(l for l in arg_locs if isinstance(l, Register))
        yield RegisterUseDef(defs=arg_regs)

        for arg_loc, arg2 in zip(arg_locs, args):
            arg = arg2[1]
            if isinstance(arg_loc, Register):
                yield self.move(arg, arg_loc)
            elif isinstance(arg_loc, StackLocation):
                pass
            else:  # pragma: no cover
                raise NotImplementedError('Parameters in memory not impl')

    def gen_function_exit(self, rv):
        live_out = set()
        if rv:
            retval_loc = self.determine_rv_location(rv[0])
            yield self.move(retval_loc, rv[1])
            live_out.add(retval_loc)
        yield RegisterUseDef(uses=live_out)

    def determine_arg_locations(self, arg_types):
        """
            Given a set of argument types, determine location for argument
            ABI:
            pass args in R12-R17
            return values in R10
        """
        locations = []
        regs = [R12, R13, R14, R15, R16, R17]
        offset = 0
        for a in arg_types:
            if a.is_blob:
                r = StackLocation(offset, a.size)
                offset += a.size
            else:
                if regs:
                    r = regs.pop(0)
                else:
                    arg_size = self.info.get_size(a)
                    r = StackLocation(offset, arg_size)
                    offset += arg_size
            locations.append(r)
        return locations

    def determine_rv_location(self, ret_type):
        rv = R10
        return rv

    def gen_prologue(self, frame):
        """ Returns prologue instruction sequence """
        # Label indication function:
        yield Label(frame.name)
        ssize = round_up(frame.stacksize + 8)
        if self.has_option('rvc') and isinsrange(10, -ssize):
            yield CAddi16sp(-ssize)  # Reserve stack space
        else:
            yield Addi(SP, SP, -ssize)  # Reserve stack space            
        
        if self.has_option('rvc'):
            yield CSwsp(LR, 4)
            yield CSwsp(FP, 0)
        else:
            yield Sw(LR, 4, SP)
            yield Sw(FP, 0, SP)
        
        if self.has_option('rvc'):
            yield CAddi4spn(FP, 8)  # Setup frame pointer
        else:
            yield Addi(FP, SP, 8)  # Setup frame pointer        
        #yield Addi(FP, SP, 8)  # Setup frame pointer        
        
        rsize = 0
        for register in self.callee_save:
            if frame.is_used(register):
                rsize += 4 
        rsize = round_up(rsize)         
        if self.has_option('rvc') and isinsrange(10, rsize):
            yield CAddi16sp(-rsize)  # Reserve stack space
        else:
            yield Addi(SP, SP, -rsize)  # Reserve stack space
        i = 0
        for register in self.callee_save:
            if frame.is_used(register):
                i -= 4
                if self.has_option('rvc'):
                    yield CSwsp(register,i + rsize)
                else:
                    yield Sw(register, i + rsize, SP)
        

        # Allocate space for outgoing calls:
        extras = max(frame.out_calls) if frame.out_calls else 0
        if extras:
            ssize = round_up(extras)
            if self.has_option('rvc') and isinsrange(10, ssize):
                yield CAddi16sp(-ssize)  # Reserve stack space
            else:
                yield Addi(SP, SP, -ssize)  # Reserve stack space            

    def litpool(self, frame):
        """ Generate instruction for the current literals """
        yield Section('data')
        # Align at 4 byte
        if frame.constants:
            yield Align(4)

        # Add constant literals:
        while frame.constants:
            label, value = frame.constants.pop(0)
            yield Label(label)
            if isinstance(value, (int, str)):
                yield dcd(value)
            elif isinstance(value, bytes):
                for byte in value:
                    yield DByte(byte)
                yield Align(4)  # Align at 4 bytes
            else:  # pragma: no cover
                raise NotImplementedError('Constant of type {}'.format(value))
        
        yield Section('code')

    def between_blocks(self, frame):
        for ins in self.litpool(frame):
            yield ins

    def gen_epilogue(self, frame):
        """ Return epilogue sequence for a frame. Adjust frame pointer
            and add constant pool
        """
        # Free space for outgoing calls:
        extras = max(frame.out_calls) if frame.out_calls else 0
        if extras:
            ssize = round_up(extras)            
            if self.has_option('rvc') and isinsrange(10, ssize):
                yield CAddi16sp(ssize)  # Reserve stack space
            else:
                yield Addi(SP, SP, ssize)  # Reserve stack space            
        # Callee saved registers:
        rsize = 0
        for register in self.callee_save:
            if frame.is_used(register):
                rsize += 4 
        rsize = round_up(rsize)
        
        i = 0
        for register in self.callee_save:
            if frame.is_used(register):
                i -= 4
                if self.has_option('rvc'):
                    yield CLwsp(register, i + rsize)
                else:
                    yield Lw(register, i + rsize, SP)              
               
        if self.has_option('rvc') and isinsrange(10, rsize):
            yield CAddi16sp(rsize)  # Reserve stack space
        else:
            yield Addi(SP, SP, rsize)  # Reserve stack space              
        
        if self.has_option('rvc'):
            yield CLwsp(LR, 4)
            yield CLwsp(FP, 0)
        else:
            yield Lw(LR, 4, SP)
            yield Lw(FP, 0, SP)
        
        ssize = round_up(frame.stacksize + 8) 
        if self.has_option('rvc') and isinsrange(10, ssize):
            yield CAddi16sp(ssize)  # Free stack space
        else:
            yield Addi(SP, SP, ssize)  # Free stack space
            
        # Return
        if self.has_option('rvc'):
            yield CJr(LR)
        else:
            yield Blr(R0, LR, 0)

        # Add final literal pool:
        for instruction in self.litpool(frame):
            yield instruction
        yield Align(4)  # Align at 4 bytes


def round_up(s):
    return s + (16 - s % 16)
