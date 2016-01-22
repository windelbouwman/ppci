import unittest
from ppci.arch.isa import Instruction, Syntax, register_argument


class TestInstruction1(Instruction):
    rg = register_argument('rg', str)
    syntax = Syntax(['inc', rg])


class TestInstruction2(Instruction):
    pass


class IsaTestCase(unittest.TestCase):
    def test_bad_instantiation(self):
        with self.assertRaises(AssertionError):
            TestInstruction1()

    def test_instruction_repr(self):
        instruction = TestInstruction2()
        self.assertTrue(str(instruction))

    def test_property_repr(self):
        self.assertTrue(str(TestInstruction1.rg))

    def test_syntax_repr(self):
        self.assertTrue(str(TestInstruction1.syntax))

    def test_invalid_field(self):
        instruction = TestInstruction2()
        with self.assertRaises(KeyError):
            instruction.set_field([], 'x', 123)


if __name__ == '__main__':
    unittest.main()
