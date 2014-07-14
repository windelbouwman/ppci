from ..basetarget import Target
from ...assembler import BaseAssembler
from .registers import rax, rcx, rdx, rbx, rsp, rbp, rsi, rdi
from .registers import r8, r9, r10, r11, r12, r13, r14, r15, regs64
from .instructions import Mov, Inc, Xor, Push, Pop


class X86Assembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)
        self.make_parser()


class X86Target(Target):
    """ x86 target containing assembler, linker"""
    def __init__(self):
        super().__init__('x86')

        for reg in regs64:
            self.add_keyword(reg.name)

        self.add_rule('reg', ['rax'], lambda rhs: rax)
        self.add_rule('reg', ['rcx'], lambda rhs: rcx)
        self.add_rule('reg', ['rdx'], lambda rhs: rdx)
        self.add_rule('reg', ['rbx'], lambda rhs: rbx)
        self.add_rule('reg', ['rsp'], lambda rhs: rsp)
        self.add_rule('reg', ['rbp'], lambda rhs: rbp)
        self.add_rule('reg', ['rsi'], lambda rhs: rsi)
        self.add_rule('reg', ['rdi'], lambda rhs: rdi)
        self.add_rule('reg', ['r8'], lambda rhs: r8)
        self.add_rule('reg', ['r9'], lambda rhs: r9)
        self.add_rule('reg', ['r10'], lambda rhs: r10)
        self.add_rule('reg', ['r11'], lambda rhs: r11)
        self.add_rule('reg', ['r12'], lambda rhs: r12)
        self.add_rule('reg', ['r13'], lambda rhs: r13)
        self.add_rule('reg', ['r14'], lambda rhs: r14)
        self.add_rule('reg', ['r15'], lambda rhs: r15)

        self.add_keyword('mov')
        self.add_instruction(['mov', 'reg', ',', 'reg'],
                             lambda rhs: Mov(rhs[1], rhs[3]))

        self.add_keyword('xor')
        self.add_instruction(['xor', 'reg', ',', 'reg'],
                             lambda rhs: Xor(rhs[1], rhs[3]))

        self.add_keyword('inc')
        self.add_instruction(['inc', 'reg'],
                             lambda rhs: Inc(rhs[1]))

        self.add_keyword('push')
        self.add_instruction(['push', 'reg'],
                             lambda rhs: Push(rhs[1]))

        self.add_keyword('pop')
        self.add_instruction(['pop', 'reg'],
                             lambda rhs: Pop(rhs[1]))

        self.assembler = X86Assembler(self)
