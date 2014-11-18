import unittest
import sys
from ppci.gen_sled import Spec, Generator, pattern, Constructor
from ppci.gen_sled import Token


class SledTestCase(unittest.TestCase):
    def testSpecApi(self):
        """ Drive the cpu spec api.
            Take as an example the arm add instruction.
        """
        spec = Spec()

        # Tokens and fields:
        tok = Token(32)
        spec.add_token(tok)
        rd = tok.add_field('rd', 13, 14)
        rm = tok.add_field('rm', 13, 14)
        rn = tok.add_field('rn', 13, 14)
        opcode = tok.add_field('opcode', 21, 28)
        cond = tok.add_field('cond', 28, 31)
        S = tok.add_field('S', 20, 20)

        # Patterns:
        add = pattern('add', 0b100)
        r0 = pattern('R0', 0)
        r1 = pattern('R1', 1)
        r2 = pattern('R2', 2)
        reg = Constructor('reg', [])
        # , [R0 | R1 | R2], None)

        # Specify add instruction:
        add = Constructor('add', [tok])
        rn = add.add_parameter('rn', reg)
        rm = add.add_parameter('rm', reg)
        rd = add.add_parameter('rd', reg)
        add.syntax = ['add', rn, ',', rm, ',', rd]
        add.assign(S, 1)
        add.assign(opcode, 0x100)
        add.assign(cond, 0xe)
        spec.add_constructor(add)

        # Create new instance:
        add1 = add(r1, r2, r0)
        print('new ins:', add1)
        #self.assertEqual(bytes([0xe, 0x82, 0x10, 0x0]), add1.encode())

        # Generate things?
        sg = Generator()
        #target = sg.generate(spec)

        # Generated code usage:
        #parse("add r1, r2, r0")
        #decode(0xe0821000)


if __name__ == '__main__':
    unittest.main()
    sys.exit()
