import unittest
from ppci.arch.isa import Instruction, Syntax, register_argument
from ppci.arch import example


class DummyInstruction1(Instruction):
    rg = register_argument('rg', str)
    syntax = Syntax(['inc', rg])


class DummyInstruction2(Instruction):
    pass


class IsaTestCase(unittest.TestCase):
    def test_bad_instantiation(self):
        with self.assertRaises(AssertionError):
            DummyInstruction1()

    def test_instruction_repr(self):
        instruction = DummyInstruction2()
        self.assertTrue(str(instruction))

    def test_property_repr(self):
        self.assertTrue(str(DummyInstruction1.rg))

    def test_syntax_repr(self):
        self.assertTrue(str(DummyInstruction1.syntax))

    def test_invalid_field(self):
        instruction = DummyInstruction2()
        with self.assertRaises(KeyError):
            instruction.set_field([], 'x', 123)

    def test_replace_register(self):
        """ Test the replace register function """
        add = example.Add(example.R1, example.R2, example.R3)
        add.replace_register(example.R2, example.R6)
        self.assertIs(example.R1, add.rd)
        self.assertIs(example.R6, add.rm)

    def test_replace_register_not_used(self):
        add = example.Add(example.R1, example.R2, example.R3)
        add.replace_register(example.R4, example.R6)
        self.assertIs(example.R1, add.rd)
        self.assertIs(example.R2, add.rm)


if __name__ == '__main__':
    unittest.main()
