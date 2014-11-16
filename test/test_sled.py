import unittest
import sys
from ppci.gen_sled import Spec, Generator, pattern, constructor, Field
from ppci.gen_sled import Token, Assignment, assign


class SledTestCase(unittest.TestCase):
    def testSpecApi(self):
        """ Drive the cpu spec api """
        spec = Spec()

        # Tokens and fields:
        tok = Token(32)
        spec.add_token(tok)
        rd = Field(tok, 13, 14)
        rm = Field(tok, 13, 14)
        rn = Field(tok, 13, 14)
        opcode = Field(tok, 21, 28)
        cond = Field(tok, 28, 31)
        S = Field(tok, 16, 16)

        # Patterns:
        add = pattern('add', 0b100)
        sub = pattern('sub', 0b10)
        gt = pattern('gt', 0x5)
        al = pattern('', 0xe)
        R0 = pattern('R0', 0)
        R1 = pattern('R1', 1)
        R2 = pattern('R2', 2)
        reg = R0 | R1 | R2
        reg._name = 'reg'

        alu_op = assign(cond, al) | assign(S, pattern('', 0))
        # alu = constructor({opcode: Add | Sub}) ^ constructor({cond: Cond})
        # | Orr | And
        add = constructor('add', [assign(opcode, add), assign(rd, reg), ',', assign(rn, reg), ',', assign(rm, reg)], alu_op)
        sub = constructor('sub', [assign(opcode, sub), assign(rd, reg), ',', assign(rn, reg), ',', assign(rm, reg)], alu_op)

        spec.add_constructor(add)
        spec.add_constructor(sub)
        sg = Generator()
        sg.generate(spec)


if __name__ == '__main__':
    unittest.main()
    sys.exit()
