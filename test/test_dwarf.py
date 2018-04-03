
import unittest
from ppci.utils.dwarf import line as lnp


class LineNumberProgramTestCase(unittest.TestCase):
    def test_use_case(self):
        program = lnp.LineNumberProgram([
            lnp.Copy(),
            lnp.Copy(),
            lnp.SetColumn(6),
            lnp.Copy(),
            lnp.AdvanceLine(2),
            lnp.Copy(),
            lnp.AdvancePc(2),
            lnp.Copy(),
            lnp.NegateStmt(),
            lnp.Copy(),
        ])
        program.show()
        program.run()
        print(program.encode())


if __name__ == '__main__':
    unittest.main()
