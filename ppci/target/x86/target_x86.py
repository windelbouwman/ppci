"""
    X86-64 target description.
"""

from ..basetarget import Target
from ...assembler import BaseAssembler
from .registers import rax, rcx, rdx, rbx, rsp, rbp, rsi, rdi
from .registers import r8, r9, r10, r11, r12, r13, r14, r15, regs64
from .instructions import isa, reloc_map


class X86Assembler(BaseAssembler):
    def __init__(self, target):
        super().__init__(target)

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

        self.parser.add_rule('strrr', ['ID'], lambda rhs: rhs[0].val)

        for reg in regs64:
            self.add_keyword(reg.name)

        # Add isa instructions:
        self.gen_asm_parser(isa)

        self.add_keyword('jmp')
        self.add_keyword('call')
        self.add_keyword('ret')
        self.add_keyword('int')
        self.add_keyword('jmpshort')
        self.add_keyword('mov')
        self.add_keyword('xor')
        self.add_keyword('inc')
        self.add_keyword('push')
        self.add_keyword('pop')
        self.add_keyword('add')
        self.add_keyword('sub')
        self.add_keyword('cmp')
        self.add_keyword('imul')


class X86Target(Target):
    """ x86 target containing assembler, linker"""
    def __init__(self):
        super().__init__('x86')

        self.reloc_map = reloc_map
        self.assembler = X86Assembler(self)
