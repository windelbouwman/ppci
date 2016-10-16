import unittest
from ppci.arch.encoding import Syntax
from ppci.arch.avr import instructions as avr_instructions
from ppci.arch.avr import registers as avr_registers
from ppci.arch.arm import arm_instructions
from ppci.arch.arm import registers as arm_registers


class SyntaxTestCase(unittest.TestCase):
    def test_lower_case(self):
        """ A TypeError is raised when syntax contains mixed casing """
        with self.assertRaises(TypeError):
            Syntax(['Ab', 'bf'])


class DecodeTestCase(unittest.TestCase):
    def test_decode_nop(self):
        """ Check nop decoding """
        instruction = avr_instructions.Nop.decode(bytes([0, 0]))
        self.assertIsInstance(instruction, avr_instructions.Nop)

    def test_decode_not_enough(self):
        """ Check that decoding with too few data raises an error """
        with self.assertRaisesRegex(ValueError, 'Not enough data'):
            avr_instructions.Nop.decode(bytes([0]))

    def test_decode_too_much(self):
        """ Check that decoding with too much data raises an error """
        with self.assertRaisesRegex(ValueError, 'Too much data'):
            avr_instructions.Nop.decode(bytes([0, 1, 2]))

    def test_decode_invalid_nop(self):
        """ Check that a wrong bit pattern cannot be decoded """
        with self.assertRaisesRegex(ValueError, 'Cannot decode'):
            avr_instructions.Nop.decode(bytes([2, 2]))

    def test_decode_avr_add(self):
        """ This is a more difficult case, because off the register args """
        instruction = avr_instructions.Add.decode(bytes([0x12, 0xC]))
        self.assertIsInstance(instruction, avr_instructions.Add)
        self.assertIs(avr_registers.r1, instruction.rd)
        self.assertIs(avr_registers.r2, instruction.rr)

    def test_decode_avr_add_2(self):
        """ This is a more difficult case, because off the register args """
        instruction = avr_instructions.Add.decode(bytes([0x12, 0xE]))
        self.assertIsInstance(instruction, avr_instructions.Add)
        self.assertIs(avr_registers.r1, instruction.rd)
        self.assertIs(avr_registers.r18, instruction.rr)

    def test_decode_avr_in(self):
        """ An even more difficult case """
        instruction = avr_instructions.In.decode(bytes([0x72, 0xb0]))
        self.assertIsInstance(instruction, avr_instructions.In)
        self.assertIs(avr_registers.r7, instruction.rd)
        self.assertEqual(2, instruction.na)

    def test_decode_adiw(self):
        """ Test decode with a transformed value """
        instruction = avr_instructions.Adiw.decode(bytes([0x11, 0x96]))
        self.assertIs(avr_registers.X, instruction.rd)
        self.assertEqual(1, instruction.imm)

    def test_decode_arm_cmp(self):
        """ An even more difficult case, with a sub constructor """
        instruction = arm_instructions.Cmp2.decode(
            bytes([0x2b, 0x02, 0x54, 0xe1]))
        self.assertIsInstance(instruction, arm_instructions.Cmp2)
        self.assertIs(arm_registers.R4, instruction.rn)
        self.assertEqual(arm_registers.R11, instruction.rm)
        self.assertIsInstance(instruction.shift, arm_instructions.ShiftLsr)
        self.assertEqual(4, instruction.shift.n)

    def test_decode_variable_size(self):
        """ The hardest case with optional tokens """
        pass


if __name__ == '__main__':
    unittest.main()
